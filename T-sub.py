# -*- coding: utf-8 -*-
"""
T-sub - 节点订阅汇总工具
功能：
1. 从指定URL获取节点配置
2. 合并多个源的节点
3. 生成包含所有节点的订阅文件
"""
import os
import sys
import logging
import argparse
from datetime import datetime
import time

# 配置日志
sys.stdout.reconfigure(encoding='utf-8')
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("T-sub.log", encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# 导入自定义模块
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from config_loader import ConfigLoader
from node.node_processor import NodeProcessor

class SubscriptionManager:
    """订阅管理器，负责协调节点处理和文件生成"""
    
    def __init__(self, config, output_dir=None):
        self.config = config
        self.output_dir = output_dir or "subscriptions_output"
        self._ensure_output_dir()
    
    def _ensure_output_dir(self):
        """确保输出目录存在"""
        try:
            if not os.path.exists(self.output_dir):
                os.makedirs(self.output_dir, exist_ok=True)
                logger.info(f"已创建输出目录: {self.output_dir}")
        except Exception as e:
            logger.error(f"创建输出目录失败: {str(e)}")
    
    def _get_output_path(self, filename):
        """获取文件的完整输出路径"""
        return os.path.join(self.output_dir, filename)
    
    def process_subscriptions(self):
        """处理订阅，包括获取、合并节点和生成文件"""
        start_time = time.time()
        
        try:
            # 创建节点处理器实例
            processor = NodeProcessor(self.config)
            
            # 合并节点
            nodes = processor.merge_nodes()
            
            if not nodes:
                logger.error("未能获取任何节点，请检查网络连接或源地址是否有效")
                return
            
            # 生成订阅文件到指定目录
            output_path = self._get_output_path(self.config["OUTPUT_ALL_FILE"])
            processor.generate_subscription_file(nodes, output_path)
            
            elapsed_time = time.time() - start_time
            logger.info(f"=== T-sub 节点订阅汇总工具运行完成 ===")
            logger.info(f"所有节点处理完成，共生成{len(nodes)}个节点的订阅")
            logger.info(f"总耗时: {elapsed_time:.2f} 秒")
        except Exception as e:
            logger.error(f"处理订阅时发生错误: {str(e)}")
            import traceback
            traceback.print_exc()

def main():
    # 添加命令行参数解析
    parser = argparse.ArgumentParser(description='T-sub 节点订阅汇总工具')
    parser.add_argument('--output', '-o', default='subscriptions_output', help='输出目录，默认为subscriptions_output')
    parser.add_argument('--debug', action='store_true', help='启用调试模式')
    args = parser.parse_args()
    
    # 如果启用调试模式，设置日志级别为DEBUG
    if args.debug:
        for handler in logger.handlers:
            handler.setLevel(logging.DEBUG)
        logger.setLevel(logging.DEBUG)
    
    logger.info("=== T-sub 节点订阅汇总工具启动 ===")
    logger.info(f"当前时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"输出目录: {args.output}")
    
    try:
        # 加载配置
        config_loader = ConfigLoader()
        config = config_loader.load_config()
        
        # 创建订阅管理器实例
        manager = SubscriptionManager(config, args.output)
        
        # 处理订阅
        manager.process_subscriptions()
    except KeyboardInterrupt:
        logger.info("程序被用户中断")
    except Exception as e:
        logger.error(f"程序运行出错: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()