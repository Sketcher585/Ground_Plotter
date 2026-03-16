import sys
if sys.prefix == '/usr':
    sys.real_prefix = sys.prefix
    sys.prefix = sys.exec_prefix = '/home/yashika-khandelwal/workspace_ros2/install/diff_drive_sim'
