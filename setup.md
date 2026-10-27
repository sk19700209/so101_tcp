# セットアップ方法

Ubuntu 22.04 に ROS 2 Humble・Gazebo Fortress・ReazonSpeech を入れ、so101_tcp を動かすまでの手順。
GPU不要。マイク要。

## 1. ROS 2 Humbleインストール

```bash
sudo apt install -y software-properties-common curl
sudo add-apt-repository universe

export ROS_APT_SOURCE_VERSION=$(curl -s https://api.github.com/repos/ros-infrastructure/ros-apt-source/releases/latest | grep -F "tag_name" | awk -F\" '{print $4}')
curl -L -o /tmp/ros2-apt-source.deb "https://github.com/ros-infrastructure/ros-apt-source/releases/download/${ROS_APT_SOURCE_VERSION}/ros2-apt-source_${ROS_APT_SOURCE_VERSION}.$(. /etc/os-release && echo $VERSION_CODENAME)_all.deb"
sudo dpkg -i /tmp/ros2-apt-source.deb

sudo apt update
sudo apt install -y ros-humble-desktop python3-colcon-common-extensions
echo "source /opt/ros/humble/setup.bash" >> ~/.bashrc
source ~/.bashrc
```

うまくいかないときは [公式のインストール手順](https://docs.ros.org/en/humble/Installation/Ubuntu-Install-Debs.html) を確認。

## 2. Gazebo Fortress と必要なものをインストール

```bash
sudo apt install -y ros-humble-ros-gz python3-pip libportaudio2 git
pip install "numpy<2" ikpy sounddevice sherpa-onnx
```

`ros-humble-ros-gz` で Gazebo Fortress もインストール。
`numpy<2` は ROS 2 Humble と相性合わせ。

## 3. 音声認識（ReazonSpeech）インストール

```bash
cd ~
git clone https://github.com/reazon-research/ReazonSpeech
pip install ReazonSpeech/pkg/k2-asr
```

GPU 不要。モデル本体は初回起動時に Hugging Face から自動でダウンロードされるので、初回だけネット接続が必要。

## 4. ワークスペースを作ってビルド

```bash
mkdir -p ~/ros2_ws/src
cd ~/ros2_ws/src
unzip ~/Downloads/so101_tcp.zip
cd ~/ros2_ws
colcon build --packages-select so101_tcp
source install/setup.bash
```

## 5. 起動

```bash
ros2 launch so101_tcp so101_tcp.launch.py
```

Gazebo が開き、ターミナルに「話しかけてください」と出たら、マイクに向かって話す。

| 声で言う例 | 動作 |
| --- | --- |
| 前 / 後ろ | 手先を前 / 後ろへ 3 cm |
| 左 / 右 | 手先を左 / 右へ 3 cm |
| 上げて / 下げて | 手先を上 / 下へ 3 cm |
| 開いて / 閉じて | グリッパーを開く / 閉じる |
| ホーム | ホーム姿勢に戻る |

「前、それから左」のように続けて言うと、順番に実行する。

新しいターミナルを開いたときは、`source ~/ros2_ws/install/setup.bash` を実行。
