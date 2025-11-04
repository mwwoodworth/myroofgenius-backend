#!/usr/bin/env python3
"""
Test Operating System Implementation
Verify kernel, memory, and file system functionality
"""

import requests
import json
from datetime import datetime
from colorama import init, Fore, Style
import time

init(autoreset=True)

BASE_URL = "https://brainops-backend-prod.onrender.com"
LOCAL_URL = "http://localhost:10000"

# Use local for testing during development
API_URL = LOCAL_URL

def test_kernel():
    """Test kernel functionality"""
    print(f"\n{Fore.CYAN}{'='*60}")
    print(f"{Fore.CYAN}TESTING OS KERNEL")
    print(f"{Fore.CYAN}{'='*60}\n")
    
    results = {"passed": 0, "failed": 0}
    
    # Test kernel status
    print(f"{Fore.YELLOW}Testing kernel status...")
    try:
        response = requests.get(f"{API_URL}/api/v1/os/kernel/status", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"{Fore.GREEN}✅ Kernel status: operational")
            print(f"   CPU count: {data.get('cpu', {}).get('count')}")
            print(f"   Memory: {data.get('memory', {}).get('total', 0)/(1024**3):.2f}GB")
            print(f"   Processes: {data.get('processes')}")
            print(f"   Uptime: {data.get('uptime', 0):.0f} seconds")
            results["passed"] += 1
        else:
            print(f"{Fore.RED}❌ Kernel status failed: {response.status_code}")
            results["failed"] += 1
    except Exception as e:
        print(f"{Fore.RED}❌ Kernel status error: {e}")
        results["failed"] += 1
    
    # Test process creation
    print(f"\n{Fore.YELLOW}Testing process creation...")
    try:
        process_data = {
            "command": "echo",
            "args": ["Hello from OS"],
            "priority": "normal"
        }
        response = requests.post(f"{API_URL}/api/v1/os/process/create", 
                                json=process_data, timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"{Fore.GREEN}✅ Process created")
            print(f"   PID: {data.get('pid')}")
            print(f"   Name: {data.get('name')}")
            print(f"   State: {data.get('state')}")
            results["passed"] += 1
            
            # Store PID for later tests
            test_pid = data.get('pid')
        else:
            print(f"{Fore.RED}❌ Process creation failed: {response.status_code}")
            results["failed"] += 1
            test_pid = None
    except Exception as e:
        print(f"{Fore.RED}❌ Process creation error: {e}")
        results["failed"] += 1
        test_pid = None
    
    # Test process list
    print(f"\n{Fore.YELLOW}Testing process list...")
    try:
        response = requests.get(f"{API_URL}/api/v1/os/process/list", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"{Fore.GREEN}✅ Process list retrieved")
            print(f"   Total processes: {data.get('total')}")
            processes = data.get('processes', [])
            for proc in processes[:3]:
                print(f"   - PID {proc['pid']}: {proc['name']} ({proc['state']})")
            results["passed"] += 1
        else:
            print(f"{Fore.RED}❌ Process list failed: {response.status_code}")
            results["failed"] += 1
    except Exception as e:
        print(f"{Fore.RED}❌ Process list error: {e}")
        results["failed"] += 1
    
    return results

def test_memory():
    """Test memory management"""
    print(f"\n{Fore.CYAN}{'='*60}")
    print(f"{Fore.CYAN}TESTING MEMORY MANAGEMENT")
    print(f"{Fore.CYAN}{'='*60}\n")
    
    results = {"passed": 0, "failed": 0}
    
    # Test memory stats
    print(f"{Fore.YELLOW}Testing memory statistics...")
    try:
        response = requests.get(f"{API_URL}/api/v1/os/memory/stats", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"{Fore.GREEN}✅ Memory stats retrieved")
            print(f"   Total: {data.get('total', 0)/(1024**3):.2f}GB")
            print(f"   Used: {data.get('used', 0)/(1024**3):.2f}GB")
            print(f"   Free: {data.get('free', 0)/(1024**3):.2f}GB")
            print(f"   Page faults: {data.get('page_faults')}")
            results["passed"] += 1
        else:
            print(f"{Fore.RED}❌ Memory stats failed: {response.status_code}")
            results["failed"] += 1
    except Exception as e:
        print(f"{Fore.RED}❌ Memory stats error: {e}")
        results["failed"] += 1
    
    # Test memory allocation
    print(f"\n{Fore.YELLOW}Testing memory allocation...")
    try:
        alloc_data = {
            "size": 4096,
            "process_id": 1,
            "region_type": "heap",
            "strategy": "best_fit"
        }
        response = requests.post(f"{API_URL}/api/v1/os/memory/allocate", 
                                json=alloc_data, timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"{Fore.GREEN}✅ Memory allocated")
            print(f"   Address: {data.get('address')}")
            print(f"   Size: {data.get('size')} bytes")
            results["passed"] += 1
            
            # Store address for deallocation
            test_address = data.get('address')
        else:
            print(f"{Fore.RED}❌ Memory allocation failed: {response.status_code}")
            results["failed"] += 1
            test_address = None
    except Exception as e:
        print(f"{Fore.RED}❌ Memory allocation error: {e}")
        results["failed"] += 1
        test_address = None
    
    # Test memory deallocation
    if test_address:
        print(f"\n{Fore.YELLOW}Testing memory deallocation...")
        try:
            response = requests.post(f"{API_URL}/api/v1/os/memory/deallocate", 
                                    params={"address": test_address, "process_id": 1}, 
                                    timeout=10)
            if response.status_code == 200:
                print(f"{Fore.GREEN}✅ Memory deallocated")
                results["passed"] += 1
            else:
                print(f"{Fore.RED}❌ Memory deallocation failed: {response.status_code}")
                results["failed"] += 1
        except Exception as e:
            print(f"{Fore.RED}❌ Memory deallocation error: {e}")
            results["failed"] += 1
    
    return results

def test_filesystem():
    """Test file system"""
    print(f"\n{Fore.CYAN}{'='*60}")
    print(f"{Fore.CYAN}TESTING FILE SYSTEM")
    print(f"{Fore.CYAN}{'='*60}\n")
    
    results = {"passed": 0, "failed": 0}
    
    # Test file system info
    print(f"{Fore.YELLOW}Testing file system info...")
    try:
        response = requests.get(f"{API_URL}/api/v1/os/fs/info", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"{Fore.GREEN}✅ File system info retrieved")
            print(f"   Type: {data.get('type')}")
            print(f"   Block size: {data.get('block_size')} bytes")
            print(f"   Total blocks: {data.get('total_blocks')}")
            print(f"   Free blocks: {data.get('free_blocks')}")
            results["passed"] += 1
        else:
            print(f"{Fore.RED}❌ File system info failed: {response.status_code}")
            results["failed"] += 1
    except Exception as e:
        print(f"{Fore.RED}❌ File system info error: {e}")
        results["failed"] += 1
    
    # Test directory creation
    print(f"\n{Fore.YELLOW}Testing directory creation...")
    try:
        dir_data = {
            "path": "/test_dir",
            "mode": 0o755,
            "uid": 0,
            "gid": 0
        }
        response = requests.post(f"{API_URL}/api/v1/os/fs/directory/create", 
                                json=dir_data, timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"{Fore.GREEN}✅ Directory created")
            print(f"   Path: {data.get('path')}")
            print(f"   Inode: {data.get('inode')}")
            results["passed"] += 1
        else:
            print(f"{Fore.RED}❌ Directory creation failed: {response.status_code}")
            results["failed"] += 1
    except Exception as e:
        print(f"{Fore.RED}❌ Directory creation error: {e}")
        results["failed"] += 1
    
    # Test file creation
    print(f"\n{Fore.YELLOW}Testing file creation...")
    try:
        file_data = {
            "path": "/test_dir/test_file.txt",
            "mode": 0o644,
            "uid": 0,
            "gid": 0
        }
        response = requests.post(f"{API_URL}/api/v1/os/fs/file/create", 
                                json=file_data, timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"{Fore.GREEN}✅ File created")
            print(f"   Path: {data.get('path')}")
            print(f"   Inode: {data.get('inode')}")
            results["passed"] += 1
        else:
            print(f"{Fore.RED}❌ File creation failed: {response.status_code}")
            results["failed"] += 1
    except Exception as e:
        print(f"{Fore.RED}❌ File creation error: {e}")
        results["failed"] += 1
    
    # Test directory listing
    print(f"\n{Fore.YELLOW}Testing directory listing...")
    try:
        response = requests.get(f"{API_URL}/api/v1/os/fs/list", 
                               params={"path": "/test_dir"}, timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"{Fore.GREEN}✅ Directory listed")
            print(f"   Path: {data.get('path')}")
            entries = data.get('entries', [])
            for entry in entries:
                print(f"   - {entry['name']} ({entry['type']})")
            results["passed"] += 1
        else:
            print(f"{Fore.RED}❌ Directory listing failed: {response.status_code}")
            results["failed"] += 1
    except Exception as e:
        print(f"{Fore.RED}❌ Directory listing error: {e}")
        results["failed"] += 1
    
    return results

def test_os_dashboard():
    """Test OS dashboard"""
    print(f"\n{Fore.CYAN}{'='*60}")
    print(f"{Fore.CYAN}TESTING OS DASHBOARD")
    print(f"{Fore.CYAN}{'='*60}\n")
    
    results = {"passed": 0, "failed": 0}
    
    print(f"{Fore.YELLOW}Testing OS dashboard...")
    try:
        response = requests.get(f"{API_URL}/api/v1/os/dashboard", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"{Fore.GREEN}✅ OS dashboard retrieved")
            
            # Kernel info
            kernel = data.get('kernel', {})
            print(f"\n   Kernel:")
            print(f"   - Uptime: {kernel.get('uptime', 0):.0f} seconds")
            print(f"   - Processes: {kernel.get('processes')}")
            print(f"   - Threads: {kernel.get('threads')}")
            
            # CPU info
            cpu = data.get('cpu', {})
            print(f"\n   CPU:")
            print(f"   - Count: {cpu.get('count')}")
            print(f"   - Usage: {cpu.get('percent')}%")
            print(f"   - Load avg: {cpu.get('load_avg')}")
            
            # Memory info
            memory = data.get('memory', {})
            print(f"\n   Memory:")
            print(f"   - Total: {memory.get('total', 0)/(1024**3):.2f}GB")
            print(f"   - Used: {memory.get('used', 0)/(1024**3):.2f}GB")
            print(f"   - Free: {memory.get('free', 0)/(1024**3):.2f}GB")
            print(f"   - Usage: {memory.get('percent', 0):.1f}%")
            
            # File system info
            fs = data.get('filesystem', {})
            print(f"\n   File System:")
            print(f"   - Type: {fs.get('type')}")
            print(f"   - Used: {fs.get('percent_used', 0):.1f}%")
            print(f"   - Open files: {fs.get('open_files')}")
            
            results["passed"] += 1
        else:
            print(f"{Fore.RED}❌ OS dashboard failed: {response.status_code}")
            results["failed"] += 1
    except Exception as e:
        print(f"{Fore.RED}❌ OS dashboard error: {e}")
        results["failed"] += 1
    
    # Test OS health
    print(f"\n{Fore.YELLOW}Testing OS health...")
    try:
        response = requests.get(f"{API_URL}/api/v1/os/health", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"{Fore.GREEN}✅ OS health: {'Healthy' if data.get('healthy') else 'Unhealthy'}")
            
            components = data.get('components', {})
            print(f"   Components:")
            for comp, status in components.items():
                print(f"   - {comp}: {status}")
            
            metrics = data.get('metrics', {})
            print(f"   Metrics:")
            print(f"   - CPU: {metrics.get('cpu_percent')}%")
            print(f"   - Memory: {metrics.get('memory_percent')}%")
            print(f"   - Processes: {metrics.get('processes')}")
            
            results["passed"] += 1
        else:
            print(f"{Fore.RED}❌ OS health failed: {response.status_code}")
            results["failed"] += 1
    except Exception as e:
        print(f"{Fore.RED}❌ OS health error: {e}")
        results["failed"] += 1
    
    return results

if __name__ == "__main__":
    print(f"{Fore.MAGENTA}{'='*60}")
    print(f"{Fore.MAGENTA}OPERATING SYSTEM TEST SUITE")
    print(f"{Fore.MAGENTA}Testing Complete OS Implementation")
    print(f"{Fore.MAGENTA}Target: {API_URL}")
    print(f"{Fore.MAGENTA}Time: {datetime.now().isoformat()}")
    print(f"{Fore.MAGENTA}{'='*60}")
    
    # Test all components
    kernel_results = test_kernel()
    memory_results = test_memory()
    fs_results = test_filesystem()
    dashboard_results = test_os_dashboard()
    
    # Calculate totals
    total_passed = (kernel_results["passed"] + memory_results["passed"] + 
                   fs_results["passed"] + dashboard_results["passed"])
    total_failed = (kernel_results["failed"] + memory_results["failed"] + 
                   fs_results["failed"] + dashboard_results["failed"])
    total_tests = total_passed + total_failed
    success_rate = (total_passed / total_tests * 100) if total_tests > 0 else 0
    
    # Final verdict
    print(f"\n{Fore.CYAN}{'='*60}")
    print(f"{Fore.CYAN}TEST RESULTS")
    print(f"{Fore.CYAN}{'='*60}")
    print(f"{Fore.GREEN}✅ Passed: {total_passed}")
    print(f"{Fore.RED}❌ Failed: {total_failed}")
    print(f"{Fore.CYAN}📊 Success Rate: {success_rate:.1f}%")
    
    if success_rate >= 80:
        print(f"\n{Fore.GREEN}🚀 OPERATING SYSTEM FULLY OPERATIONAL!")
        print(f"{Fore.GREEN}Kernel, memory management, and file system working")
    elif success_rate >= 60:
        print(f"\n{Fore.YELLOW}⚠️  OPERATING SYSTEM PARTIALLY OPERATIONAL")
        print(f"{Fore.YELLOW}Some components need attention")
    else:
        print(f"\n{Fore.RED}❌ OPERATING SYSTEM NEEDS FIXES")
        print(f"{Fore.RED}Critical components not functioning")
    
    print(f"\n{Fore.CYAN}Test completed at {datetime.now().isoformat()}")
    print(f"{Fore.CYAN}{'='*60}\n")