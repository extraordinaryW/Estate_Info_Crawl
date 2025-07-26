# -*- coding: utf-8 -*-
"""
数据存储工具模块
"""
import pandas as pd
import os
import requests
from typing import Dict, List, Any, Optional
from config import Config

class DataStorage:
    """数据存储类"""
    
    @staticmethod
    def save_to_excel(data: List[Dict[str, Any]], filename: str, sheet_name: str = "Sheet1") -> None:
        """
        保存数据到Excel文件
        
        Args:
            data: 要保存的数据列表
            filename: 文件名
            sheet_name: 工作表名称
        """
        if not data:
            print("没有数据需要保存")
            return
        
        filepath = os.path.join(Config.OUTPUT_DIR, filename)
        
        # 创建DataFrame
        df = pd.DataFrame(data)
        
        # 保存到Excel
        try:
            with pd.ExcelWriter(filepath, mode='a', engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name=sheet_name, index=False)
            print(f"数据已保存到: {filepath}")
        except FileNotFoundError:
            # 如果文件不存在，直接创建
            df.to_excel(filepath, sheet_name=sheet_name, index=False)
            print(f"数据已保存到: {filepath}")
    
    @staticmethod
    def save_to_csv(data: List[Dict[str, Any]], filename: str) -> None:
        """
        保存数据到CSV文件
        
        Args:
            data: 要保存的数据列表
            filename: 文件名
        """
        if not data:
            print("没有数据需要保存")
            return
        
        filepath = os.path.join(Config.OUTPUT_DIR, filename)
        
        # 创建DataFrame
        df = pd.DataFrame(data)
        
        # 保存到CSV
        df.to_csv(filepath, index=False, encoding='utf-8-sig')
        print(f"数据已保存到: {filepath}")
    
    @staticmethod
    def download_file(url: str, filepath: str) -> bool:
        """
        下载文件
        
        Args:
            url: 文件URL
            filepath: 保存路径
            
        Returns:
            bool: 下载是否成功
        """
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            # 确保目录存在
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            
            with open(filepath, "wb") as f:
                f.write(response.content)
            
            return True
        except Exception as e:
            print(f"下载文件失败 {url}: {e}")
            return False
    
    @staticmethod
    def create_folder(folder_path: str) -> str:
        """
        创建文件夹
        
        Args:
            folder_path: 文件夹路径
            
        Returns:
            str: 创建的文件夹路径
        """
        full_path = os.path.join(Config.OUTPUT_DIR, folder_path)
        os.makedirs(full_path, exist_ok=True)
        return full_path
    
    @staticmethod
    def append_to_excel(data: List[Dict[str, Any]], filename: str, sheet_name: str = "Sheet1") -> None:
        """
        追加数据到Excel文件
        
        Args:
            data: 要追加的数据列表
            filename: 文件名
            sheet_name: 工作表名称
        """
        if not data:
            print("没有数据需要追加")
            return
        
        filepath = os.path.join(Config.OUTPUT_DIR, filename)
        
        # 创建DataFrame
        df = pd.DataFrame(data)
        
        try:
            # 尝试读取现有文件
            existing_df = pd.read_excel(filepath, sheet_name=sheet_name)
            # 合并数据
            combined_df = pd.concat([existing_df, df], ignore_index=True)
            # 保存
            with pd.ExcelWriter(filepath, mode='w', engine='openpyxl') as writer:
                combined_df.to_excel(writer, sheet_name=sheet_name, index=False)
        except FileNotFoundError:
            # 如果文件不存在，直接创建
            df.to_excel(filepath, sheet_name=sheet_name, index=False)
        
        print(f"数据已追加到: {filepath}") 