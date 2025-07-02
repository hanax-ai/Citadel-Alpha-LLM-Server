#!/usr/bin/env python3

"""
PLANB-01 Ubuntu Installation Validation Test
============================================

This test validates the current state of PLANB-01 Ubuntu installation
and identifies remaining configuration tasks.

Usage: python3 tests/validation/test_planb_01_validation.py
"""

import os
import subprocess
import socket
import sys
from pathlib import Path
from typing import Dict, List, Tuple


class PLANB01Validator:
    """Validates PLANB-01 Ubuntu installation state."""
    
    def __init__(self):
        self.results = {}
        self.warnings = []
        self.errors = []
        
    def run_command(self, cmd: str) -> Tuple[bool, str]:
        """Run a shell command and return success status and output."""
        try:
            result = subprocess.run(
                cmd, 
                shell=True, 
                capture_output=True, 
                text=True, 
                timeout=30
            )
            return result.returncode == 0, result.stdout.strip()
        except subprocess.TimeoutExpired:
            return False, "Command timed out"
        except Exception as e:
            return False, str(e)

    def check_os_version(self) -> bool:
        """Verify Ubuntu 24.04 LTS installation."""
        success, output = self.run_command("lsb_release -a")
        if success and "Ubuntu 24.04" in output:
            self.results["os_version"] = "✅ Ubuntu 24.04 LTS detected"
            return True
        else:
            self.errors.append("❌ Ubuntu 24.04 LTS not detected")
            return False

    def check_hostname(self) -> bool:
        """Verify hostname configuration."""
        hostname = socket.gethostname()
        if hostname == "llm":
            self.results["hostname"] = "✅ Hostname correctly set to 'llm'"
            return True
        else:
            self.warnings.append(f"⚠️ Hostname is '{hostname}', expected 'llm'")
            return False

    def check_network_config(self) -> bool:
        """Verify network configuration."""
        success, output = self.run_command("ip addr show")
        if success and "192.168.10.29" in output:
            self.results["network"] = "✅ Network configured as LLM node (192.168.10.29)"
            return True
        else:
            self.errors.append("❌ Expected IP 192.168.10.29 not found")
            return False

    def check_hardware_detection(self) -> bool:
        """Verify hardware detection."""
        checks = {}
        
        # CPU check
        success, output = self.run_command("lscpu | grep 'Model name'")
        if success and "Intel" in output:
            checks["cpu"] = "✅ CPU detected: " + output.split(":", 1)[1].strip()
        elif success and "AMD" in output:
            checks["cpu"] = "✅ CPU detected: " + output.split(":", 1)[1].strip()
        else:
            checks["cpu"] = "❌ CPU detection failed"

        # Memory check
        success, output = self.run_command("free -h | grep Mem")
        if success:
            memory_info = output.split()[1]
            if "G" in memory_info:
                checks["memory"] = f"✅ Memory detected: {memory_info}"
            else:
                checks["memory"] = "⚠️ Memory detection unclear"
        else:
            checks["memory"] = "❌ Memory detection failed"

        # GPU check
        success, output = self.run_command("lspci | grep -i nvidia")
        if success and output:
            # Count unique GPUs by filtering for VGA/3D controller entries
            gpu_lines = [line for line in output.split('\n') if line and ('VGA' in line or '3D controller' in line)]
            gpu_count = len(gpu_lines)
            
            if gpu_count >= 2:
                checks["gpu"] = f"✅ {gpu_count} NVIDIA GPUs detected"
            elif gpu_count == 1:
                checks["gpu"] = f"✅ {gpu_count} NVIDIA GPU detected"
            else:
                checks["gpu"] = f"⚠️ NVIDIA hardware detected but no GPUs identified"
        else:
            checks["gpu"] = "❌ NVIDIA GPUs not detected"

        self.results.update(checks)
        return all("✅" in check for check in checks.values())

    def check_storage_layout(self) -> bool:
        """Verify storage configuration."""
        checks = {}
        
        # Check primary storage
        success, output = self.run_command("lsblk")
        if success:
            if "nvme0n1" in output:
                checks["primary_storage"] = "✅ Primary NVMe (nvme0n1) detected"
            else:
                checks["primary_storage"] = "❌ Primary NVMe (nvme0n1) not found"
                
            if "nvme1n1" in output:
                if "/mnt/citadel-models" in output:
                    checks["model_storage"] = "✅ Model storage mounted at /mnt/citadel-models"
                else:
                    checks["model_storage"] = "⚠️ nvme1n1 detected but not mounted as model storage"
            else:
                checks["model_storage"] = "❌ Secondary NVMe (nvme1n1) not found"
                
            if "sda" in output:
                if "/mnt/citadel-backup" in output:
                    checks["backup_storage"] = "✅ Backup storage mounted at /mnt/citadel-backup"
                else:
                    checks["backup_storage"] = "⚠️ sda detected but not mounted as backup storage"
            else:
                checks["backup_storage"] = "❌ Backup drive (sda) not found"
        else:
            checks["storage_detection"] = "❌ Storage detection failed"

        # Check root filesystem utilization
        success, output = self.run_command("df -h / | tail -1")
        if success:
            usage_parts = output.split()
            if len(usage_parts) >= 4:
                total_size = usage_parts[1]
                if "G" in total_size and int(total_size.replace("G", "")) < 150:
                    checks["root_size"] = "⚠️ Root filesystem appears small - LVM expansion needed"
                else:
                    checks["root_size"] = f"✅ Root filesystem size: {total_size}"

        self.results.update(checks)
        return "/mnt/citadel-models" in str(self.results) and "/mnt/citadel-backup" in str(self.results)

    def check_user_configuration(self) -> bool:
        """Verify user and permissions."""
        checks = {}
        
        # Check current user
        current_user = os.getenv("USER", "unknown")
        if current_user == "agent0":
            checks["user"] = "✅ Running as user 'agent0'"
        else:
            checks["user"] = f"⚠️ Running as user '{current_user}', expected 'agent0'"

        # Check sudo group membership
        success, output = self.run_command("groups")
        if success and "sudo" in output:
            checks["sudo_access"] = "✅ User has sudo privileges"
        else:
            checks["sudo_access"] = "⚠️ Sudo group membership unclear"

        self.results.update(checks)
        return "agent0" in str(checks.get("user", ""))

    def check_network_connectivity(self) -> bool:
        """Verify network connectivity."""
        checks = {}
        
        # Internet connectivity
        success, _ = self.run_command("ping -c 2 google.com")
        if success:
            checks["internet"] = "✅ Internet connectivity working"
        else:
            checks["internet"] = "❌ Internet connectivity failed"

        # DNS resolution
        success, _ = self.run_command("nslookup google.com")
        if success:
            checks["dns"] = "✅ DNS resolution working"
        else:
            checks["dns"] = "❌ DNS resolution failed"

        self.results.update(checks)
        return success

    def check_essential_packages(self) -> bool:
        """Check if essential packages are installed."""
        # Map package names to their command names
        package_commands = {
            "curl": "curl",
            "wget": "wget",
            "git": "git",
            "vim": "vim",
            "htop": "htop",
            "tree": "tree",
            "python3-pip": "pip3"  # python3-pip package provides pip3 command
        }
        checks = {}
        
        for package, command in package_commands.items():
            success, _ = self.run_command(f"which {command}")
            if success:
                checks[f"pkg_{package}"] = f"✅ {package} installed"
            else:
                checks[f"pkg_{package}"] = f"❌ {package} not installed"

        self.results.update(checks)
        return all("✅" in check for check in checks.values())

    def check_completion_script(self) -> bool:
        """Verify completion script exists and is executable."""
        script_path = Path("scripts/complete-planb-01-setup.sh")
        if script_path.exists():
            if os.access(script_path, os.X_OK):
                self.results["completion_script"] = "✅ Completion script ready for execution"
                return True
            else:
                self.warnings.append("⚠️ Completion script exists but not executable")
                return False
        else:
            self.errors.append("❌ Completion script not found")
            return False

    def generate_recommendations(self) -> List[str]:
        """Generate actionable recommendations based on validation results."""
        recommendations = []
        
        # Check if storage needs configuration
        storage_issues = [k for k, v in self.results.items() 
                         if "storage" in k and ("❌" in v or "⚠️" in v)]
        if storage_issues:
            recommendations.append(
                "🔧 CRITICAL: Configure secondary storage using completion script"
            )

        # Check if packages need installation
        package_issues = [k for k, v in self.results.items() 
                         if "pkg_" in k and "❌" in v]
        if package_issues:
            recommendations.append(
                "📦 Install missing essential packages using completion script"
            )

        # Check if completion script can be run
        if "completion_script" in self.results and "✅" in self.results["completion_script"]:
            recommendations.append(
                "🚀 READY: Execute 'sudo ./scripts/complete-planb-01-setup.sh'"
            )

        return recommendations

    def run_validation(self) -> Dict:
        """Run complete validation suite."""
        print("🔍 PLANB-01 Ubuntu Installation Validation")
        print("=" * 50)
        
        validation_tests = [
            ("OS Version", self.check_os_version),
            ("Hostname", self.check_hostname),
            ("Network Configuration", self.check_network_config),
            ("Hardware Detection", self.check_hardware_detection),
            ("Storage Layout", self.check_storage_layout),
            ("User Configuration", self.check_user_configuration),
            ("Network Connectivity", self.check_network_connectivity),
            ("Essential Packages", self.check_essential_packages),
            ("Completion Script", self.check_completion_script),
        ]
        
        passed_tests = 0
        total_tests = len(validation_tests)
        
        for test_name, test_func in validation_tests:
            print(f"\n🧪 Testing: {test_name}")
            try:
                result = test_func()
                if result:
                    passed_tests += 1
                    print(f"   ✅ PASSED")
                else:
                    print(f"   ⚠️ ISSUES FOUND")
            except Exception as e:
                print(f"   ❌ ERROR: {e}")
                self.errors.append(f"Test '{test_name}' failed: {e}")

        print("\n" + "=" * 50)
        print("📊 VALIDATION SUMMARY")
        print("=" * 50)
        
        # Print all results
        for category, result in self.results.items():
            print(f"  {result}")
        
        # Print warnings and errors
        if self.warnings:
            print("\n⚠️ WARNINGS:")
            for warning in self.warnings:
                print(f"  {warning}")
        
        if self.errors:
            print("\n❌ ERRORS:")
            for error in self.errors:
                print(f"  {error}")
        
        # Generate recommendations
        recommendations = self.generate_recommendations()
        if recommendations:
            print("\n🎯 RECOMMENDATIONS:")
            for i, rec in enumerate(recommendations, 1):
                print(f"  {i}. {rec}")
        
        # Overall status
        success_rate = (passed_tests / total_tests) * 100
        print(f"\n📈 OVERALL STATUS: {passed_tests}/{total_tests} tests passed ({success_rate:.1f}%)")
        
        if success_rate >= 80:
            print("🎉 PLANB-01 foundation is solid - ready for completion!")
        elif success_rate >= 60:
            print("⚠️ PLANB-01 partially complete - run completion script")
        else:
            print("❌ PLANB-01 requires significant work - review errors")
        
        return {
            "passed_tests": passed_tests,
            "total_tests": total_tests,
            "success_rate": success_rate,
            "results": self.results,
            "warnings": self.warnings,
            "errors": self.errors,
            "recommendations": recommendations
        }


def main():
    """Main execution function."""
    validator = PLANB01Validator()
    return validator.run_validation()


if __name__ == "__main__":
    results = main()
    # Exit with error code if validation fails significantly
    sys.exit(0 if results["success_rate"] >= 50 else 1)