import rclpy
from rclpy.lifecycle import Node, Publisher, State, TransitionCallbackReturn
from std_msgs.msg import String
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import os

class CodeFileHandler(FileSystemEventHandler):
    def __init__(self, publish_cb, logger):
        self.publish_cb = publish_cb
        self.logger = logger

    def on_modified(self, event):
        if not event.is_directory and event.src_path.endswith('.stl'):
            self.logger.info(f"Detected modification in: {event.src_path}")
            # Симуляция чтения файла
            self.publish_cb(f"Content of {event.src_path}")

class FileWatcherNode(Node):
    def __init__(self):
        super().__init__('file_watcher_node')
        self.pub_: Publisher = None
        self.observer = None
        
        self.declare_parameter('watch_dir', '/tmp/code_debug/')

    def on_configure(self, state: State) -> TransitionCallbackReturn:
        self.get_logger().info('FSM Transition: Configuring FileWatcherNode...')
        self.pub_ = self.create_lifecycle_publisher(String, '/sens/raw_code_stream', 10)
        
        self.watch_dir = self.get_parameter('watch_dir').get_parameter_value().string_value
        os.makedirs(self.watch_dir, exist_ok=True)
        return TransitionCallbackReturn.SUCCESS

    def on_activate(self, state: State) -> TransitionCallbackReturn:
        self.get_logger().info('FSM Transition: Activating FileWatcherNode (debug_file mode)...')
        super().on_activate(state)
        
        # Запускаем фоновый поток Watchdog
        handler = CodeFileHandler(self.publish_code, self.get_logger())
        self.observer = Observer()
        self.observer.schedule(handler, self.watch_dir, recursive=False)
        self.observer.start()
        
        return TransitionCallbackReturn.SUCCESS

    def on_deactivate(self, state: State) -> TransitionCallbackReturn:
        self.get_logger().info('FSM Transition: Deactivating FileWatcherNode... Going to sleep.')
        # Останавливаем сбор данных
        if self.observer:
            self.observer.stop()
            self.observer.join()
            self.observer = None
        super().on_deactivate(state)
        return TransitionCallbackReturn.SUCCESS

    def on_cleanup(self, state: State) -> TransitionCallbackReturn:
        self.get_logger().info('FSM Transition: Cleaning up FileWatcherNode...')
        if self.pub_:
            self.destroy_publisher(self.pub_)
        return TransitionCallbackReturn.SUCCESS

    def on_shutdown(self, state: State) -> TransitionCallbackReturn:
        self.get_logger().info('FSM Transition: Shutting down FileWatcherNode...')
        if self.observer:
            self.observer.stop()
            self.observer.join()
        return TransitionCallbackReturn.SUCCESS

    def publish_code(self, content: str):
        # Публикуем данные ТОЛЬКО если узел активирован
        if self.pub_ and self.pub_.is_activated:
            msg = String()
            msg.data = content
            self.pub_.publish(msg)
            self.get_logger().info('Published updated STL code to /sens/raw_code_stream.')

def main(args=None):
    rclpy.init(args=args)
    node = FileWatcherNode()
    rclpy.spin(node)
    rclpy.shutdown()

if __name__ == '__main__':
    main()
