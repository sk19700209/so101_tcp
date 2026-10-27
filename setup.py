from glob import glob
from setuptools import setup

pkg = 'so101_tcp'
setup(
    name=pkg,
    version='0.0.1',
    packages=[pkg],
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + pkg]),
        ('share/' + pkg, ['package.xml']),
        ('share/' + pkg + '/launch', glob('launch/*.py')),
        ('share/' + pkg + '/config', glob('config/*.yaml')),
        ('share/' + pkg + '/urdf', glob('urdf/*.urdf') + ['urdf/LICENSE.SO-ARM100']),
        ('share/' + pkg + '/urdf/assets', glob('urdf/assets/*')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    entry_points={'console_scripts': [
        'tcp_controller = so101_tcp.tcp_controller:main',
        'voice_command = so101_tcp.voice_command:main',
    ]},
)
