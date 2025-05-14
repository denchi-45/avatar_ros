import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32
import pygame

from .avatar import AvatarFace

INTERVAL = 30


class AvatarNode(Node):
    def __init__(self):
        super().__init__('avatar')

        self.avatar = AvatarFace()

        self.mouth_subscription = self.create_subscription(
            Float32,
            'mouth',
            self.callback_mouth,
            10
        )

        self.timer = self.create_timer(
            INTERVAL / 1000, self.update)

        self.clock = pygame.time.Clock()

    def callback_mouth(self, msg):
        self.get_logger().info('Received mouth data: %f' % msg.data)
        self.avatar.face_renderer.current_context['mouth']['open'] = msg.data

    def update(self):
        if not self.avatar.is_alive():
            self.destroy_node()
            return

        self.avatar.loop()
        self.clock.tick(1000 // INTERVAL)


def main(args=None):
    rclpy.init(args=args)
    pygame.init()
    node = AvatarNode()
    node.avatar.begin()

    while rclpy.ok() and node.avatar.is_alive():
        rclpy.spin_once(node)
    node.get_logger().info("Shutting down")
    node.destroy_node()
    pygame.quit()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
