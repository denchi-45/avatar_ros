import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32
from geometry_msgs.msg import Point
import pygame

from .avatar import AvatarFace

INTERVAL = 30


class AvatarNode(Node):
    def __init__(self):
        super().__init__('avatar')

        self.avatar = AvatarFace()

        # Subscriptions
        self.mouth_subscription = self.create_subscription(
            Float32,
            'mouth',
            self.callback_mouth,
            10
        )

        # Publishers
        self.left_gaze_publisher = self.create_publisher(
            Point,
            'left_eye_gaze',
            10
        )
        self.right_gaze_publisher = self.create_publisher(
            Point,
            'right_eye_gaze',
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

        # Publish gaze data
        left_gaze = Point()
        left_gaze.x = self.avatar.face_renderer.current_context['eyes']['left']['gazeX']
        left_gaze.y = self.avatar.face_renderer.current_context['eyes']['left']['gazeY']
        left_gaze.z = 0.0
        self.left_gaze_publisher.publish(left_gaze)

        right_gaze = Point()
        right_gaze.x = self.avatar.face_renderer.current_context['eyes']['right']['gazeX']
        right_gaze.y = self.avatar.face_renderer.current_context['eyes']['right']['gazeY']
        right_gaze.z = 0.0
        self.right_gaze_publisher.publish(right_gaze)

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
