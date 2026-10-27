import queue

import numpy as np
import rclpy
import sounddevice as sd
from rclpy.node import Node
from std_msgs.msg import String
from reazonspeech.k2.asr import load_model, transcribe, audio_from_numpy

RATE = 16000
BLOCK = 1600
THRESHOLD = 0.03
SILENCE_BLOCKS = 6
MAX_BLOCKS = 50
WORDS = [
    ('home', ['ホーム', 'フォーム', '最初', '初期']),
    ('back', ['後ろ', 'うしろ']),
    ('forward', ['前', 'まえ']),
    ('left', ['左', 'ひだり']),
    ('right', ['右', 'みぎ']),
    ('up', ['上げ', 'あげ', '上', 'うえ']),
    ('down', ['下げ', 'さげ', '下', 'した']),
    ('open', ['開', 'ひら', 'あけ']),
    ('close', ['閉', 'とじ', 'しめ']),
]


def parse(text):
    cmds = []
    i = 0
    while i < len(text):
        for cmd, words in WORDS:
            hit = next((w for w in words if text.startswith(w, i)), None)
            if hit:
                cmds.append(cmd)
                i += len(hit)
                break
        else:
            i += 1
    return cmds


class VoiceCommand(Node):
    def __init__(self):
        super().__init__('voice_command')
        self.pub = self.create_publisher(String, '/so101/command', 10)
        self.get_logger().info('ReazonSpeech モデルを読み込み中...')
        self.model = load_model(device='cpu', precision='int8', language='ja')
        self.q = queue.Queue()
        self.get_logger().info('話しかけてください（例：右、上げて、開いて）')

    def on_audio(self, indata, frames, time, status):
        self.q.put(indata[:, 0].copy())

    def listen(self):
        buf, silent = [], 0
        with sd.InputStream(samplerate=RATE, blocksize=BLOCK, channels=1,
                            dtype='float32', callback=self.on_audio):
            while rclpy.ok():
                block = self.q.get()
                loud = np.sqrt(np.mean(block ** 2)) > THRESHOLD
                if not (loud or buf):
                    continue
                buf.append(block)
                silent = 0 if loud else silent + 1
                if silent >= SILENCE_BLOCKS or len(buf) >= MAX_BLOCKS:
                    self.recognize(np.concatenate(buf))
                    buf, silent = [], 0
                    while not self.q.empty():
                        self.q.get_nowait()

    def recognize(self, audio):
        text = transcribe(self.model, audio_from_numpy(audio, RATE)).text
        cmds = parse(text)
        self.get_logger().info(f'認識: 「{text}」 -> {cmds}')
        for cmd in cmds:
            self.pub.publish(String(data=cmd))


def main():
    rclpy.init()
    node = VoiceCommand()
    try:
        node.listen()
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
