# Citadel AI OS Plan B - Task Backlog

**Purpose**: Track discoveries, todos, and future enhancements identified during implementation  
**Last Updated**: 2025-01-07  

## Discoveries from PLANB-01 Analysis

### ✅ **Critical IP Address Correction**
**Discovery**: Task documentation referenced wrong IP (192.168.10.35) vs actual deployment (192.168.10.29)  
**Impact**: High - Documentation inconsistency resolved  
**Action**: Corrected in task documentation and aligned with actual LLM server purpose  

### ✅ **Hardware Upgrade Identification**
**Discovery**: Actual hardware exceeds specifications  
- **Expected**: Dell Precision 3630, Intel Xeon  
- **Actual**: MSI MS-7E34, Intel Core Ultra 9 285K (24 cores)  
**Impact**: Positive - Better AI performance capability  
**Action**: Documentation updated to reflect actual specs  

### ⚠️ **LVM Underutilization Issue**
**Discovery**: Primary drive (3.6TB) only using 100GB in LVM  
**Impact**: Significant storage waste  
**Todo**: Expand LVM volumes during PLANB-01 completion  
**Priority**: High  

### ⚠️ **Documentation Alignment Gap**
**Discovery**: README.md has IP/server role inconsistencies identified in analysis  
**Impact**: Medium - Could cause deployment confusion  
**Todo**: Update README.md after PLANB-01 completion  
**Priority**: Medium  

## Future Enhancements Identified

### 🔮 **Automated Validation Pipeline**
**Idea**: Create comprehensive validation suite for all PLANB tasks  
**Benefit**: Consistent quality assurance across deployment phases  
**Implementation**: Extend test framework in `/tests/validation/`  
**Priority**: Low  

### 🔮 **Configuration Management**
**Idea**: Centralized configuration using pydantic settings classes  
**Benefit**: Type-safe, validated configuration across all components  
**Implementation**: Create `/configs/` based classes following project rules  
**Priority**: Medium  

### 🔮 **Performance Monitoring Dashboard**
**Idea**: Real-time monitoring for LLM server performance  
**Benefit**: Operational visibility and troubleshooting  
**Implementation**: Integrate with PLANB-08 monitoring setup  
**Priority**: Low  

## Technical Debt

### 🔧 **PLANB-02 Backup Cron Validation Issue**
**Issue**: Backup cron job validation test failing (9/10 tests passing)
**Symptom**: "Could not check cron jobs" error in validation script
**Impact**: Low - backup functionality likely working, validation test issue
**Location**: `test_backup_cron()` method in [`tests/test_planb_02_validation.py`](../tests/test_planb_02_validation.py)
**Fix**: Investigate cron job detection method and update validation logic
**Priority**: Low
**Date Added**: 2025-01-07

### 🔧 **Script Permission Consistency**
**Issue**: Not all scripts have consistent executable permissions
**Fix**: Standardize script permissions in `/scripts/`
**Priority**: Low

### 🔧 **Error Handling Enhancement**
**Issue**: Some scripts could have more robust error handling
**Fix**: Add comprehensive error handling and recovery procedures
**Priority**: Medium

## PLANB-02+ Preparation Notes

### 📋 **Storage Configuration Prerequisites**
- Secondary drives (nvme1n1, sda) ready for configuration
- Mount points already defined in completion script
- UUIDs will be dynamically generated during formatting

### 📋 **NVIDIA Driver Considerations**
- Dual RTX 4070 Ti SUPER configuration verified
- PCIe slots properly detected
- IOMMU support configured in GRUB settings

### 📋 **Python Environment Planning**
- Python 3.12 target confirmed
- Virtual environment strategy needed for vLLM isolation
- Package management approach required

## Observations

### 💡 **Positive Findings**
1. **Hardware Detection**: Excellent compatibility with Ubuntu 24.04
2. **Network Configuration**: Proper Hana-X Lab integration
3. **User Setup**: Correct permissions and sudo access
4. **Modularity**: Task breakdown allows incremental progress

### ⚠️ **Risk Areas**
1. **Storage Complexity**: Multiple drives require careful configuration
2. **NVIDIA Drivers**: GPU setup can be complex in Ubuntu
3. **vLLM Dependencies**: Framework has specific requirements
4. **Production Hardening**: Security and performance tuning needed

---

*This backlog captures insights and future work identified during PLANB-01 analysis and will be updated as implementation progresses.*