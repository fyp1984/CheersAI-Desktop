"""
文件格式转换插件主入口
Document Format Exporter Plugin for Dify
"""
from dify_plugin import DifyPluginEnv, Plugin

# Create plugin instance
plugin = Plugin(DifyPluginEnv())

if __name__ == "__main__":
    # Run the plugin
    plugin.run()
