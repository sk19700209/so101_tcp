import os
import warnings
from collections import deque

import numpy as np
import rclpy
from rclpy.node import Node
from std_msgs.msg import Float64, String
from ament_index_python.packages import get_package_share_directory
from ikpy.chain import Chain

warnings.filterwarnings('ignore', module='ikpy')

ARM_JOINTS = ['shoulder_pan', 'shoulder_lift', 'elbow_flex', 'wrist_flex', 'wrist_roll']
CHAIN = ['base_link', 'shoulder_pan', 'shoulder_link', 'shoulder_lift', 'upper_arm_link',
         'elbow_flex', 'lower_arm_link', 'wrist_flex', 'wrist_link', 'wrist_roll',
         'gripper_link', 'gripper_frame_joint', 'gripper_frame_link']
ACTIVE = [False, True, True, True, True, False, False]
STEP = 0.03
HOME = np.array([0.0, 0.0, -0.5, 0.5, 1.0, 0.0, 0.0])
MOVES = {'forward': (STEP, 0, 0), 'back': (-STEP, 0, 0),
         'left': (0, STEP, 0), 'right': (0, -STEP, 0),
         'up': (0, 0, STEP), 'down': (0, 0, -STEP)}
GRIP_OPEN, GRIP_CLOSE = 1.0, 0.0
PERIOD = 0.05
MOVE_TICKS = 20
PAUSE_TICKS = 10


class TcpController(Node):
    def __init__(self):
        super().__init__('tcp_controller')
        urdf = os.path.join(get_package_share_directory('so101_tcp'), 'urdf', 'so101.urdf')
        self.chain = Chain.from_urdf_file(urdf, base_elements=CHAIN, active_links_mask=ACTIVE)
        self.pubs = {n: self.create_publisher(Float64, f'/so101/{n}/cmd', 10)
                     for n in ARM_JOINTS + ['gripper']}
        self.q = HOME.copy()
        self.target = self.tcp(self.q)
        self.grip = GRIP_CLOSE
        self.queue = deque()
        self.motion = None
        self.create_subscription(String, '/so101/command', self.on_command, 10)
        self.create_timer(PERIOD, self.step)

    def tcp(self, q):
        return self.chain.forward_kinematics(q)[:3, 3]

    def on_command(self, msg):
        self.queue.append(msg.data)

    def step(self):
        if self.motion is None and self.queue:
            self.motion = self.plan(self.queue.popleft())
        if self.motion is not None:
            m = self.motion
            m['tick'] += 1
            r = min(m['tick'] / MOVE_TICKS, 1.0)
            self.q = m['q0'] + (m['q1'] - m['q0']) * r
            self.grip = m['g0'] + (m['g1'] - m['g0']) * r
            if m['tick'] >= MOVE_TICKS + PAUSE_TICKS:
                self.motion = None
        for n, v in zip(ARM_JOINTS, self.q[1:6]):
            self.pubs[n].publish(Float64(data=float(v)))
        self.pubs['gripper'].publish(Float64(data=float(self.grip)))

    def plan(self, cmd):
        q1, g1, target = self.q.copy(), self.grip, self.target
        if cmd == 'home':
            q1 = HOME.copy()
            target = self.tcp(q1)
        elif cmd == 'open':
            g1 = GRIP_OPEN
        elif cmd == 'close':
            g1 = GRIP_CLOSE
        elif cmd in MOVES:
            goal = self.target + np.array(MOVES[cmd])
            q = self.chain.inverse_kinematics(goal, initial_position=self.q)
            if np.linalg.norm(self.tcp(q) - goal) > 1e-3:
                self.get_logger().warn(f'{cmd}: 届かない位置なので無視しました')
                return None
            q1, target = q, goal
        else:
            return None
        self.target = target
        x, y, z = target
        self.get_logger().info(f'{cmd}: TCP x={x:+.3f} y={y:+.3f} z={z:+.3f} [m] grip={g1:.1f}'
                               f'（残り{len(self.queue)}件）')
        return {'tick': 0, 'q0': self.q.copy(), 'q1': q1, 'g0': self.grip, 'g1': g1}


def main():
    rclpy.init()
    node = TcpController()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
