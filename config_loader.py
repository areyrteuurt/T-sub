# -*- coding: utf-8 -*-
import os
import re
import logging

class ConfigLoader:
    """配置加载器，从配置文件读取节点源和其他设置"""
    
    def __init__(self):
        # 默认节点源列表已移除，将通过config.txt完全管理
        pass
    
    def load_config(self):
        """加载配置，优先使用config/config.txt"""
        config = {
            "SOURCES": [],
            "TIMEOUT": 5,
            "OUTPUT_ALL_FILE": "subscription_all.txt",
            "WORKERS": 10,
            "MAX_RETRY": 2
        }
        
        # 尝试多个可能的配置文件路径
        possible_paths = []
        current_dir = os.path.dirname(os.path.abspath(__file__))
        possible_paths.extend([
            os.path.join(current_dir, "config", "config.txt"),  # 使用config子目录
            os.path.join(current_dir, "config.txt"),
            "config/config.txt",
            "config.txt"
        ])
        
        # 尝试所有可能的路径
        config_loaded = False
        for path in possible_paths:
            try:
                if os.path.exists(path):
                    logging.info(f"尝试加载配置文件: {path}")
                    with open(path, 'r', encoding='utf-8') as f:
                        config["SOURCES"] = []  # 清空源列表
                        
                        for line in f:
                            line = line.strip()
                            if line.startswith('#') or not line:
                                continue
                            
                            # 解析配置项
                            if '=' in line:
                                key, value = line.split('=', 1)
                                key = key.strip()
                                value = value.strip()
                                
                                if key == "SOURCES":
                                    config[key].append(value)
                                elif key in config:
                                    if key in ["TIMEOUT", "WORKERS", "MAX_RETRY"]:
                                        try:
                                            config[key] = int(value)
                                        except ValueError:
                                            logging.warning(f"配置项 {key} 值无效，使用默认值")
                                    else:
                                        config[key] = value
                            # 简化格式：直接识别URL
                            elif re.match(r'^https?://', line):
                                config["SOURCES"].append(line)
                    
                    logging.info(f"成功加载配置文件: {path}")
                    config_loaded = True
                    break
            except Exception as e:
                logging.error(f"加载配置文件 {path} 失败: {str(e)}")
        
        # 检查是否有有效的节点源
        if not config["SOURCES"]:
            logging.warning("未找到有效的节点源，请在config.txt中添加节点源URL")
        
        logging.info(f"成功加载配置，共 {len(config['SOURCES'])} 个节点源")
        return config