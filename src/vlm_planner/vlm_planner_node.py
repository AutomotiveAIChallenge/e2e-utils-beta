#!/usr/bin/env python3
# vlm_planner_node.py

import time
import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, QoSReliabilityPolicy, QoSHistoryPolicy

from autoware_auto_planning_msgs.msg import Trajectory as OutputTrajectory
from autoware_auto_planning_msgs.msg import TrajectoryPoint as OutputPoint
from sensor_msgs.msg import Image as RosImage
from nav_msgs.msg import Odometry
from geometry_msgs.msg import AccelWithCovarianceStamped
from builtin_interfaces.msg import Duration

import cv2
from cv_bridge import CvBridge
from PIL import Image

from vlm_planner import VLMPlanner

class VlmPlannerNode(Node):
    def __init__(self):
        super().__init__('vlm_planner_node')

        self.declare_parameter('output_topic', '/output/trajectory')
        output_topic = self.get_parameter('output_topic').get_parameter_value().string_value

        self.vlm_planner = VLMPlanner(self.get_logger())

        # QoS profile settings
        reliable_qos = QoSProfile(
            reliability=QoSReliabilityPolicy.RELIABLE,
            history=QoSHistoryPolicy.KEEP_LAST,
            depth=10
        )
        
        sensor_qos = QoSProfile(
            reliability=QoSReliabilityPolicy.BEST_EFFORT,
            history=QoSHistoryPolicy.KEEP_LAST,
            depth=1
        )

        # ROS 2 Publisher & Subscribers
        self.trajectory_publisher = self.create_publisher(OutputTrajectory, output_topic, reliable_qos)
        
        self.image_sub = self.create_subscription(
            RosImage, 
            '/sensing/camera/image_raw', 
            self.image_callback, 
            sensor_qos
        )
        
        self.odometry_sub = self.create_subscription(
            Odometry,
            '/localization/kinematic_state',
            self.odometry_callback,
            reliable_qos
        )
        
        self.acceleration_sub = self.create_subscription(
            AccelWithCovarianceStamped,
            '/localization/acceleration',
            self.acceleration_callback,
            sensor_qos
        )

        self.bridge = CvBridge()
        self.latest_image = None
        self.current_odometry = None
        self.current_acceleration = None

        self.last_trajectory_action = []
        for i in range(10):
            self.last_trajectory_action.append({
                "x": float(i) * 2.5,
                "y": 0.0,
                "z": 0.0,
                "time": float(i)*0.5,
                "velocity": 5.0
            })
        self.last_inference_time_sec = time.monotonic() - 6.0
        self.inference_interval_sec = 5.0  # Inference interval (real-time 5 seconds)
        self.last_trajectory_msg = None

        self.get_logger().info(f"VLM Planner Node started. Publishing to '{output_topic}'.")

    def image_callback(self, msg: RosImage):
        """Receives camera images, saves the latest image, and generates or reuses a trajectory."""
        try:
            cv_image = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
            self.latest_image = Image.fromarray(cv2.cvtColor(cv_image, cv2.COLOR_BGR2RGB))
        except Exception as e:
            self.get_logger().error(f"Failed to convert image: {e}")
            return

        now_sec = time.monotonic()
        if (now_sec - self.last_inference_time_sec) >= self.inference_interval_sec:
            self.get_logger().info("Generating new trajectory with VLM...")

            # Get current vehicle state information
            current_velocity = 0.0
            if self.current_odometry:
                current_velocity = self.current_odometry.twist.twist.linear.x
                current_position = (self.current_odometry.pose.pose.position.x, 
                                    self.current_odometry.pose.pose.position.y,
                                    self.current_odometry.pose.pose.position.z)

            # Generate trajectory with VLM
            trajectory_points = self.vlm_planner.generate_trajectory(
                self.latest_image,
                self.last_trajectory_action,
                current_velocity,
                current_position
            )

            if len(trajectory_points) > 0:
                # On success, update result and timestamp
                self.last_inference_time_sec = now_sec
                trajectory_msg = self.create_trajectory_message(trajectory_points)
                self.last_trajectory_action = trajectory_points
                self.last_trajectory_msg = trajectory_msg
                self.trajectory_publisher.publish(trajectory_msg)
                self.get_logger().info(f"Published trajectory with {len(trajectory_points)} points")
            else:
                self.get_logger().warn("Failed to generate trajectory. No trajectory published.")
        else:
            # If 5 seconds have not passed, reuse the previous trajectory
            if self.last_trajectory_msg is not None:
                self.trajectory_publisher.publish(self.last_trajectory_msg)
                self.get_logger().info("Reusing last trajectory (interval not passed)")
            else:
                self.get_logger().warn("No previous trajectory to reuse.")

    def odometry_callback(self, msg: Odometry):
        """Receives odometry data and saves the current position and velocity information."""
        self.current_odometry = msg

    def acceleration_callback(self, msg: AccelWithCovarianceStamped):
        """Receives acceleration data and saves the current acceleration information."""
        self.current_acceleration = msg

    def create_trajectory_message(self, trajectory_points: list) -> OutputTrajectory:
        """Converts a list of trajectory points from VLM to a ROS 2 Trajectory message."""
        output_msg = OutputTrajectory()
        output_msg.header.stamp = self.get_clock().now().to_msg()
        output_msg.header.frame_id = "base_link"

        for point_data in trajectory_points:
            output_point = OutputPoint()
            
            # Set time
            time_sec = float(point_data.get("time", 0.0))
            output_point.time_from_start = Duration()
            output_point.time_from_start.sec = int(time_sec)
            output_point.time_from_start.nanosec = int((time_sec - int(time_sec)) * 1e9)
            
            # Set position
            output_point.pose.position.x = float(point_data.get("x", 0.0))
            output_point.pose.position.y = float(point_data.get("y", 0.0))
            output_point.pose.position.z = float(point_data.get("z", 0.0))
            
            # Set orientation (assume facing forward for simplicity)
            output_point.pose.orientation.x = 0.0
            output_point.pose.orientation.y = 0.0
            output_point.pose.orientation.z = 0.0
            output_point.pose.orientation.w = 1.0
            
            # Set velocity
            target_velocity = float(point_data.get("velocity", 5.0))  # Default 5 m/s
            output_point.longitudinal_velocity_mps = target_velocity
            output_point.lateral_velocity_mps = 0.0
            output_point.acceleration_mps2 = 0.0
            output_point.heading_rate_rps = 0.0
            output_point.front_wheel_angle_rad = 0.0
            output_point.rear_wheel_angle_rad = 0.0

            output_msg.points.append(output_point)

        return output_msg

def main(args=None):
    rclpy.init(args=args)
    try:
        node = VlmPlannerNode()
        rclpy.spin(node)
    except (KeyboardInterrupt, ValueError) as e:
        print(f"Node shutting down: {e}")
    finally:
        if 'node' in locals() and rclpy.ok():
            node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
