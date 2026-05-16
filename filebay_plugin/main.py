"""
FileBay Sync Plugin for Dify
Main entry point for the plugin
"""
from dify_plugin import DifyPluginEnv, Plugin

# Create plugin instance
plugin = Plugin(DifyPluginEnv())

if __name__ == "__main__":
    # Run the plugin
    plugin.run()
