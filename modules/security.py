import hashlib
import json

class Security:
    def __init__(self, config_file: str = "config/hashes.json"):
        self.config_file = config_file

    def _calculate_file_hash(self, filepath: str) -> str:
        try:
            with open(filepath, 'rb') as f:
                return hashlib.sha256(f.read()).hexdigest()
        except Exception:
            raise

    def verify_integrity(self):
        """
        验证所有文件的完整性

        Returns:
            Tuple[bool, List[str]]:
            - 是否所有文件都完整 (True/False)
            - 被篡改/缺失的文件路径列表
        """
        try:
            # 加载预期哈希值
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config_data = json.load(f)

            expected_hashes = config_data.get("file_hashes", {})
            corrupted_files = []

            # 验证每个文件的哈希值
            for filepath, expected_hash in expected_hashes.items():
                try:
                    current_hash = self._calculate_file_hash(filepath)
                    if current_hash != expected_hash:
                        corrupted_files.append(filepath)

                except Exception:
                    corrupted_files.append(filepath)

            all_valid = len(corrupted_files) == 0
            return all_valid, corrupted_files

        except Exception:
            return False, ["无法加载哈希配置文件"]