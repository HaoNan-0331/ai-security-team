#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ASG防火墙API经验管理器

功能：
1. 自动记录操作经验
2. 按错误码查询解决方案
3. 关键词搜索
4. 导出/导入经验库（分享功能）
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
import zipfile


class ExperienceManager:
    """ASG防火墙API经验管理器"""

    def __init__(self, experience_dir: str = None):
        """
        初始化经验管理器

        Args:
            experience_dir: 经验库目录路径
        """
        if experience_dir is None:
            # 默认经验库目录
            self.experience_dir = Path(__file__).parent.parent / 'experiences'
        else:
            self.experience_dir = Path(experience_dir)

        self.experience_dir.mkdir(parents=True, exist_ok=True)

        # 经验库文件路径
        self.errors_file = self.experience_dir / 'errors.json'
        self.solutions_file = self.experience_dir / 'solutions.json'
        self.auto_log_file = self.experience_dir / 'auto_log.json'

        # 加载经验库
        self.errors_db = self._load_json(self.errors_file, {})
        self.solutions_db = self._load_json(self.solutions_file, {})
        self.auto_log = self._load_json(self.auto_log_file, [])

    def _load_json(self, file_path: Path, default: Any) -> Any:
        """加载JSON文件"""
        if file_path.exists():
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"警告：加载 {file_path} 失败: {e}")
                return default
        return default

    def _save_json(self, file_path: Path, data: Any):
        """保存JSON文件"""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"错误：保存 {file_path} 失败: {e}")

    # ==================== 查询功能 ====================

    def lookup_error_code(self, code: str) -> Optional[Dict]:
        """
        查询错误码

        Args:
            code: 错误码（如 "88", "106", "250"）

        Returns:
            错误信息字典，如果不存在返回None
        """
        errors = self.errors_db.get('errors', {})
        return errors.get(code)

    def lookup_http_error(self, status_code: int) -> Optional[Dict]:
        """
        查询HTTP错误码

        Args:
            status_code: HTTP状态码

        Returns:
            错误信息字典
        """
        http_errors = self.errors_db.get('http_errors', {})
        return http_errors.get(str(status_code))

    def search_solutions(self, keyword: str) -> List[Dict]:
        """
        搜索解决方案

        Args:
            keyword: 关键词

        Returns:
            匹配的解决方案列表
        """
        keyword_lower = keyword.lower()
        results = []

        solutions = self.solutions_db.get('solutions', [])
        for sol in solutions:
            # 在标题、症状、根因中搜索
            searchable_text = (
                sol.get('title', '') + ' ' +
                ' '.join(sol.get('symptoms', [])) + ' ' +
                sol.get('root_cause', '')
            ).lower()

            if keyword_lower in searchable_text:
                results.append(sol)

        return results

    def get_solution_by_id(self, solution_id: str) -> Optional[Dict]:
        """根据ID获取解决方案"""
        solutions = self.solutions_db.get('solutions', [])
        for sol in solutions:
            if sol.get('id') == solution_id:
                return sol
        return None

    # ==================== 自动记录功能 ====================

    def log_operation(self, operation: str, endpoint: str, params: Dict,
                     data: Dict = None, response: Dict = None,
                     success: bool = None, notes: str = ""):
        """
        记录操作到自动日志

        Args:
            operation: 操作类型（如 "add_policy", "get_policies"）
            endpoint: API端点
            params: 请求参数
            data: 请求数据
            response: 响应数据
            success: 是否成功
            notes: 备注
        """
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'operation': operation,
            'endpoint': endpoint,
            'params': params,
            'data': data,
            'response_summary': self._summarize_response(response),
            'success': success if success is not None else self._is_success(response),
            'notes': notes
        }

        self.auto_log.append(log_entry)
        self._save_json(self.auto_log_file, self.auto_log)

    def _summarize_response(self, response: Dict) -> str:
        """总结响应"""
        if response is None:
            return "No response"
        if 'error' in response:
            return f"Error: {response['error']}"
        if 'code' in response:
            if response['code'] == '0':
                return "Success"
            return f"Error {response['code']}: {response.get('str', 'Unknown')}"
        if 'success' in response:
            return "Success" if response['success'] else "Failed"
        return str(response)[:100]

    def _is_success(self, response: Dict) -> bool:
        """判断响应是否成功"""
        if response is None:
            return False
        if 'error' in response:
            return False
        if 'code' in response:
            return response['code'] == '0'
        if 'success' in response:
            return response['success']
        return True

    # ==================== 经验管理功能 ====================

    def add_solution(self, solution: Dict):
        """
        添加新解决方案

        Args:
            solution: 解决方案字典
        """
        solutions = self.solutions_db.setdefault('solutions', [])

        # 检查是否已存在相同ID
        existing_ids = [s.get('id') for s in solutions]
        if solution.get('id') in existing_ids:
            raise ValueError(f"解决方案ID {solution['id']} 已存在")

        solutions.append(solution)
        self._save_json(self.solutions_file, self.solutions_db)

    def update_solution(self, solution_id: str, updates: Dict):
        """
        更新解决方案

        Args:
            solution_id: 解决方案ID
            updates: 要更新的字段
        """
        solutions = self.solutions_db.get('solutions', [])
        for sol in solutions:
            if sol.get('id') == solution_id:
                sol.update(updates)
                self._save_json(self.solutions_file, self.solutions_db)
                return True
        return False

    # ==================== 导出/导入功能 ====================

    def export_to_package(self, output_file: str = None) -> str:
        """
        导出经验库为ZIP包（分享功能）

        Args:
            output_file: 输出文件路径，默认为当前目录下的经验库包

        Returns:
            导出的文件路径
        """
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"asg_experience_pack_{timestamp}.zip"

        output_path = Path(output_file)

        with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # 添加错误码手册
            if self.errors_file.exists():
                zipf.write(self.errors_file, 'errors.json')

            # 添加解决方案库
            if self.solutions_file.exists():
                zipf.write(self.solutions_file, 'solutions.json')

            # 添加常见陷阱文档
            pitfalls_file = self.experience_dir / 'pitfalls.md'
            if pitfalls_file.exists():
                zipf.write(pitfalls_file, 'pitfalls.md')

            # 添加自动日志（可选）
            if self.auto_log_file.exists():
                zipf.write(self.auto_log_file, 'auto_log.json')

            # 创建README
            readme_content = self._generate_export_readme()
            zipf.writestr('README.md', readme_content)

        print(f"经验库已导出到: {output_path.absolute()}")
        return str(output_path.absolute())

    def _generate_export_readme(self) -> str:
        """生成导出包的README"""
        return f"""# ASG防火墙API经验库

导出时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
版本: {self.solutions_db.get('version', '1.0.0')}

## 文件说明

- **errors.json**: 错误码手册，包含所有API错误码的说明和解决方案
- **solutions.json**: 解决方案库，包含常见问题的详细解决步骤
- **pitfalls.md**: 常见陷阱文档，记录使用API时需要注意的坑点
- **auto_log.json**: 自动操作日志（如果有）

## 导入方法

使用以下命令导入此经验库：

```bash
python experience_manager.py import asg_experience_pack_xxx.zip
```

或在Python代码中：

```python
from experience_manager import ExperienceManager

mgr = ExperienceManager()
mgr.import_from_package('asg_experience_pack_xxx.zip')
```

## 使用方法

```python
from experience_manager import ExperienceManager

mgr = ExperienceManager()

# 查询错误码
error_info = mgr.lookup_error_code('88')
print(error_info)

# 搜索解决方案
solutions = mgr.search_solutions('策略添加失败')

# 获取完整解决方案
solution = mgr.get_solution_by_id('sol_001')
```

---

此经验库由 ASG防火墙API技能自动维护
"""

    def import_from_package(self, package_file: str, merge: bool = False):
        """
        从ZIP包导入经验库

        Args:
            package_file: ZIP包路径
            merge: 是否合并（True）还是覆盖（False）
        """
        package_path = Path(package_file)
        if not package_path.exists():
            raise FileNotFoundError(f"文件不存在: {package_file}")

        with zipfile.ZipFile(package_path, 'r') as zipf:
            # 列出包内文件
            files = zipf.namelist()
            print(f"经验包内容: {files}")

            # 导入错误码手册
            if 'errors.json' in files:
                if merge:
                    # 合并模式：更新现有错误码
                    existing_data = json.loads(zipf.read('errors.json'))
                    self.errors_db.setdefault('errors', {}).update(existing_data.get('errors', {}))
                    self.errors_db.setdefault('http_errors', {}).update(existing_data.get('http_errors', {}))
                else:
                    # 覆盖模式
                    self.errors_db = json.loads(zipf.read('errors.json'))
                self._save_json(self.errors_file, self.errors_db)
                print("已导入错误码手册")

            # 导入解决方案库
            if 'solutions.json' in files:
                if merge:
                    # 合并模式：添加新解决方案
                    existing_data = json.loads(zipf.read('solutions.json'))
                    existing_ids = {s.get('id') for s in self.solutions_db.get('solutions', [])}
                    for sol in existing_data.get('solutions', []):
                        if sol.get('id') not in existing_ids:
                            self.solutions_db.setdefault('solutions', []).append(sol)
                else:
                    # 覆盖模式
                    self.solutions_db = json.loads(zipf.read('solutions.json'))
                self._save_json(self.solutions_file, self.solutions_db)
                print("已导入解决方案库")

            # 导入常见陷阱文档
            if 'pitfalls.md' in files:
                content = zipf.read('pitfalls.md').decode('utf-8')
                pitfalls_file = self.experience_dir / 'pitfalls.md'
                with open(pitfalls_file, 'w', encoding='utf-8') as f:
                    f.write(content)
                print("已导入常见陷阱文档")

        print(f"经验库导入完成！")

    # ==================== 统计功能 ====================

    def get_statistics(self) -> Dict:
        """获取经验库统计信息"""
        errors = self.errors_db.get('errors', {})
        http_errors = self.errors_db.get('http_errors', {})
        solutions = self.solutions_db.get('solutions', [])

        # 统计错误码类别
        error_categories = {}
        for code, info in errors.items():
            severity = info.get('severity', 'unknown')
            error_categories[severity] = error_categories.get(severity, 0) + 1

        # 统计解决方案类别
        solution_categories = {}
        for sol in solutions:
            category = sol.get('category', 'uncategorized')
            solution_categories[category] = solution_categories.get(category, 0) + 1

        return {
            'total_error_codes': len(errors),
            'total_http_errors': len(http_errors),
            'total_solutions': len(solutions),
            'auto_log_entries': len(self.auto_log),
            'error_categories': error_categories,
            'solution_categories': solution_categories,
            'last_updated': self.solutions_db.get('last_updated', 'unknown')
        }

    def print_statistics(self):
        """打印统计信息"""
        stats = self.get_statistics()

        print("\n" + "=" * 60)
        print("ASG防火墙API经验库统计")
        print("=" * 60)
        print(f"错误码数量: {stats['total_error_codes']}")
        print(f"HTTP错误码: {stats['total_http_errors']}")
        print(f"解决方案数量: {stats['total_solutions']}")
        print(f"自动日志条目: {stats['auto_log_entries']}")
        print(f"最后更新: {stats['last_updated']}")

        print("\n错误码类别分布:")
        for category, count in stats['error_categories'].items():
            print(f"  - {category}: {count}")

        print("\n解决方案类别分布:")
        for category, count in stats['solution_categories'].items():
            print(f"  - {category}: {count}")

        print("=" * 60 + "\n")


# ==================== 命令行接口 ====================

def main():
    """命令行入口"""
    import sys

    mgr = ExperienceManager()

    if len(sys.argv) < 2:
        print("用法: python experience_manager.py <command> [args]")
        print("\n命令:")
        print("  export [output_file]   - 导出经验库为ZIP包")
        print("  import <package_file>  - 从ZIP包导入经验库")
        print("  stats                  - 显示统计信息")
        print("  search <keyword>       - 搜索解决方案")
        print("  lookup <error_code>    - 查询错误码")
        print("\n示例:")
        print("  python experience_manager.py export my_exp.zip")
        print("  python experience_manager.py import my_exp.zip")
        print("  python experience_manager.py stats")
        print("  python experience_manager.py search 策略")
        print("  python experience_manager.py lookup 88")
        sys.exit(1)

    command = sys.argv[1]

    if command == 'export':
        output_file = sys.argv[2] if len(sys.argv) > 2 else None
        mgr.export_to_package(output_file)

    elif command == 'import':
        if len(sys.argv) < 3:
            print("请指定要导入的ZIP包文件")
            sys.exit(1)
        mgr.import_from_package(sys.argv[2])

    elif command == 'stats':
        mgr.print_statistics()

    elif command == 'search':
        if len(sys.argv) < 3:
            print("请指定搜索关键词")
            sys.exit(1)
        results = mgr.search_solutions(sys.argv[2])
        print(f"\n找到 {len(results)} 个匹配的解决方案:")
        for sol in results:
            print(f"\n  [{sol.get('id')}] {sol.get('title')}")
            print(f"  类别: {sol.get('category')}")
            print(f"  症状: {', '.join(sol.get('symptoms', [])[:2])}")

    elif command == 'lookup':
        if len(sys.argv) < 3:
            print("请指定错误码")
            sys.exit(1)
        error_info = mgr.lookup_error_code(sys.argv[2])
        if error_info:
            print(f"\n错误码: {error_info.get('code')}")
            print(f"名称: {error_info.get('name')}")
            print(f"描述: {error_info.get('description')}")
            print(f"解决方案:")
            for sol in error_info.get('solutions', []):
                print(f"  - {sol}")
        else:
            print(f"未找到错误码 {sys.argv[2]} 的信息")

    else:
        print(f"未知命令: {command}")
        sys.exit(1)


if __name__ == '__main__':
    main()
