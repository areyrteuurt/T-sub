# -*- coding: utf-8 -*-
import re
import base64
import logging
import requests
import os
from concurrent.futures import ThreadPoolExecutor

class NodeProcessor:
    """节点处理器，整合节点获取和合并功能"""
    
    def __init__(self, config):
        self.config = config
        self.timeout = config.get("TIMEOUT", 5)
        self.max_retry = config.get("MAX_RETRY", 2)
        self.workers = config.get("WORKERS", 10)
    
    def fetch_nodes(self, url):
        """从指定URL获取节点列表"""
        nodes = []
        retry_count = 0
        
        while retry_count <= self.max_retry:
            try:
                logging.info(f"正在获取节点源: {url} (尝试 {retry_count + 1}/{self.max_retry + 1})")
                response = requests.get(url, timeout=self.timeout, headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                })
                response.raise_for_status()
                
                # 尝试解码响应内容
                content = response.text.strip()
                if content:
                    nodes = self._extract_nodes(content)
                    if nodes:
                        logging.info(f"成功从 {url} 获取 {len(nodes)} 个节点")
                        break
                    else:
                        logging.warning(f"从 {url} 获取内容，但未能提取到节点")
                else:
                    logging.warning(f"从 {url} 获取的内容为空")
            except Exception as e:
                logging.error(f"获取节点源 {url} 失败: {str(e)}")
            
            retry_count += 1
            if retry_count <= self.max_retry:
                logging.info(f"将在重试 {url}")
        
        return nodes
    
    def _extract_nodes(self, content):
        """从内容中提取节点信息"""
        nodes = []
        
        # 首先尝试解码Base64
        decoded_content = self._try_decode_base64(content)
        if decoded_content:
            content = decoded_content
        
        # 按行处理内容
        lines = content.split('\n')
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # 检查是否为支持的节点类型
            # 扩展支持更多节点类型，提高节点汇总率
            if re.match(r'^(vmess|v2ray|trojan|trojan-go|shadowsocks|shadowsocksr|vless|ss|ssr|hysteria|hysteria2|tuic|wireguard|naiveproxy|socks|http|https|clash|shadowsocks2|vmess\\+tls|vless\\+tls)://', line):
                nodes.append(line)
        
        return nodes
    
    def _try_decode_base64(self, content):
        """尝试解码Base64内容"""
        try:
            # 尝试直接解码
            return base64.b64decode(content).decode('utf-8')
        except:
            try:
                # 尝试添加填充后解码
                missing_padding = len(content) % 4
                if missing_padding:
                    content += '=' * (4 - missing_padding)
                return base64.b64decode(content).decode('utf-8')
            except:
                logging.debug("内容不是有效的Base64格式")
                return None
    
    def merge_nodes(self):
        """合并所有节点源"""
        all_nodes = []
        unique_nodes = set()
        
        # 获取所有节点源
        sources = self.config.get("SOURCES", [])
        if not sources:
            logging.error("没有配置节点源")
            return []
        
        logging.info(f"开始合并 {len(sources)} 个节点源")
        
        # 并发获取节点
        try:
            with ThreadPoolExecutor(max_workers=self.workers) as executor:
                results = list(executor.map(self.fetch_nodes, sources))
            
            # 合并所有节点并去重
            for nodes in results:
                for node in nodes:
                    if node not in unique_nodes:
                        unique_nodes.add(node)
                        all_nodes.append(node)
            
            logging.info(f"节点合并完成，共获取 {len(all_nodes)} 个唯一节点")
        except Exception as e:
            logging.error(f"合并节点时发生错误: {str(e)}")
            # 尝试串行获取作为备选方案
            all_nodes = self._fetch_nodes_serially(sources)
        
        return all_nodes
    
    def _fetch_nodes_serially(self, sources):
        """串行获取节点，作为并发失败的备选方案"""
        all_nodes = []
        unique_nodes = set()
        
        logging.info("尝试串行获取节点源")
        for url in sources:
            nodes = self.fetch_nodes(url)
            for node in nodes:
                if node not in unique_nodes:
                    unique_nodes.add(node)
                    all_nodes.append(node)
        
        logging.info(f"串行获取完成，共获取 {len(all_nodes)} 个唯一节点")
        return all_nodes
    
    def generate_subscription_file(self, nodes, output_file):
        """生成订阅文件"""
        try:
            if not nodes:
                logging.warning(f"没有节点可生成订阅: {output_file}")
                return None
            
            logging.info(f"准备生成订阅文件: {output_file}，包含{len(nodes)}个节点")
            
            # 将节点列表转换为字符串并编码
            nodes_text = '\n'.join(nodes)
            subscription_content = base64.b64encode(nodes_text.encode('utf-8')).decode('utf-8')
            
            # 保存到文件
            try:
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(subscription_content)
                
                # 验证文件是否成功创建
                if os.path.exists(output_file):
                    file_size = os.path.getsize(output_file)
                    if file_size > 0:
                        logging.info(f"订阅已生成: {output_file}，大小: {file_size}字节")
                    else:
                        logging.warning(f"订阅文件为空: {output_file}")
                else:
                    logging.error(f"订阅文件创建失败: {output_file}")
                
                return subscription_content
            except Exception as file_err:
                logging.error(f"写入文件失败: {str(file_err)}")
                return None
        except Exception as e:
            logging.error(f"生成订阅文件时发生未预期错误: {str(e)}")
            return None