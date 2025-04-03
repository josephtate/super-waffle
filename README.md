# RLC Cloud Repos - Cloud-Agnostic Repository Auto-Configuration

## Overview
**RLC Cloud Repos** is a **cloud-init-powered, cloud-agnostic** repository configuration utility designed to:
- Automatically **configure DNF/YUM repositories** for Rocky Linux Cloud (RLC) instances.
- **Dynamically select the best repository mirror** based on the cloud provider and region.
- **Seamlessly integrate with Cloud-Init**, ensuring repository configurations persist across reboots.
- **Deploy updates via RPM packaging**, ensuring repository configurations stay up-to-date.

## Problem Statement
Deploying Rocky Linux on various **cloud providers** (AWS, Azure, GCP, OCI) requires **custom repository configurations**:
- Different **mirror endpoints per cloud provider**.
- Ensuring mirrors **match the region** for performance and availability.
- **Fallbacks when a mirror is unavailable** (e.g., AWS instances in `us-west-1` fallback to `us-east-1`).
- Ensuring **Cloud-Init properly integrates the repository configurations** during instance boot.

### **Why This Matters**
1. **Eliminates manual repository setup** - Ensures the correct repository is auto-configured at first boot.
2. **Optimized package updates** - Selects the closest and most available repository, reducing latency.
3. **Cloud-Native Design** - Uses **Cloud-Init's metadata querying** instead of relying on hardcoded cloud provider APIs.
4. **Updatable Without Reimaging** - Repository settings can be updated dynamically via RPM package updates.

---

## **Architecture**
The system is designed as **modular components** that work together to **detect cloud provider, determine region, configure repositories, and integrate with Cloud-Init**.

### **System Flow**

```ascii
+---------------------------+
|   Instance Boots Up       |
+---------------------------+
           |
           v
+---------------------------+
| Detect Cloud Provider     |
| (Cloud-Init JSON / IMDS)  |
+---------------------------+
           |
           v
+---------------------------+
|  Detect Region            |
|  (Cloud-Init Metadata)    |
+---------------------------+
           |
           v
+---------------------------+
| Determine Repo Mirrors    |
| (Per Provider Rules)      |
+---------------------------+
           |
           v
+---------------------------+
| Configure Repo Files      |
| (/etc/yum.repos.d/)       |
+---------------------------+
```

---

### **Core Components**

#### 🟢 **Cloud Metadata Handler (`cloud_metadata.py`)**

- Reads **Cloud-Init instance-data JSON** (`/run/cloud-init/result.json`).
- Fallback: Queries **metadata service APIs** for AWS, Azure, GCP, OCI.
- Determines:
    - **Cloud Provider** (AWS, Azure, GCP, OCI).
    - **Region** (`us-west-2`, `eastus`, etc.).
    - **Fallback mirror location** (if a mirror isn't available in the detected region).

#### 🟢 **Repository Configuration Manager (`repo_config.py`)**

- Dynamically **generates `.repo` files** in `/etc/yum.repos.d/`.
- Uses **templated repository URLs**, selecting:
    - **Primary mirror** (closest to detected region).
    - **Backup mirror** (in case of failure).
- Ensures **repositories remain configured properly after reboot**.

#### 🟢 **Cloud-Init Execution Manager (`cloud_init_config.py`)**

- **Sets `$baseurl` and `$contentdir`** dynamically using cloud metadata.
- **Runs once per boot**, ensuring repo settings are up-to-date.
- Ensures **persistence** across reboots.

---

## **Implementation Details**

### 🛠️ **How It Works**

1. **Cloud-Init triggers the script** during first boot.
2. **Cloud Metadata Handler detects cloud provider & region**.
3. **Repo Config Manager selects the correct mirrors** based on geolocation.
4. **Config files are written to `/etc/yum.repos.d/`**.
5. **Settings persist between reboots**.

### 📦 **Packaging & Deployment**

- Packaged as an **RPM (`ciq-extras` repo)** for easy updates.
- Installed via `dnf` or **preloaded in cloud images**.
- Updates are deployed **without requiring new AMIs or VM images**.

---

## **Supported Cloud Providers**

| Cloud Provider | Metadata Source | Primary Mirror | Backup Mirror |
| --- | --- | --- | --- |
| **AWS** | Cloud-Init / IMDS | `depot.<region>.prod.ciqws.com` | `us-east-1` |
| **Azure** | Cloud-Init / IMDS | `eastus` | `westus2` |
| **Google** | Cloud-Init / IMDS | `Azure's closest mirror` | `westus2` |
| **Oracle** | Cloud-Init / IMDS | `us-sanjose-1` | `Azure eastus` |

---

## **Configuration & Customization**

### **Modifying Repository Selection**

- Repository mirror settings can be **overridden manually** in `/etc/ciq-repo-autoconfig.conf`.
- To disable automatic repo updates:

```bash
touch /etc/ciq-repo-disable
```

### **Manually Running the Script**

To manually trigger the configuration:

    `/usr/local/bin/rlc-cloud-repos`

## **Installation & Usage**

### **Installing via RPM**

1. Install the package:
    
    `dnf install rlc-cloud-repos`
    
2. Check that repositories are properly configured:
    
    `cat /etc/yum.repos.d/ciq.repo`

---

## **Future Enhancements**

✔ **Add support for new cloud providers** (Alibaba, OpenStack).  
✔ **Improve logging & debugging capabilities**.  
✔ **Integrate `depot-client` for advanced repository management**.

---

## 🧠 Development Notes

### 🔀 Current Development Branch

`git@github.com:ctrliq/rlc-cloud-repos.git Branch: dev`

This is the active branch for development. Use this to track commits and open PRs.

---

### ✅ What’s Locked In

- **Single touch file** at `/etc/ciq-repo-disable`
    
    - Prevents re-running config logic if it exists.
    - Created after first successful run.
    - **Removed during RPM upgrades** to allow re-run at next boot.
- **Cloud metadata detection**:
    
    - Primary: `/run/cloud-init/instance-data.json`
    - Fallback: cloud metadata service endpoints

- **Repo logic**:
    
    - Region → Mirror mapping handled via external YAML shipped in RPM
    - Template baseurl:
        
        `https://$baseurl/$contentdir/rocky-lts-$releasever.$basearch`
        
- **Repo RPM Integration**:
    
    - `%posttrans` hook to clear the disable file
    - Auto-triggers config next boot post-upgrade

---

### 📦 Region Matrix Logic

**Matrix source**: Confluence cloud region → mirror → fallback mapping.

We're controlling this via:

- A **structured YAML file** bundled in the RPM
- Can be updated without code changes
- Ensures mirror selection logic stays versioned and source-controlled

---

### 🌱 Potential FeatureRequests for Depot

- **Depot-side region detection + redirect logic**
    
    - `?provider=aws&region=us-west-2` style endpoint
    - Moves region logic out of the client, simplifies maintenance
- **Mirrorlist-style smart fallback**
    
    - Real-time mirror health + GeoIP routing
    - Similar to Fedora/CentOS mirrorlist
    - Requires discussion with Depot maintainers

---

### 🧪 Design Decision: First Boot vs Every Boot

We've **intentionally made this run only on first boot**, with control via a touch file:

- Reduces surprise side effects for downstream sysadmins
- Avoids overwriting repo config on every reboot
- Clean opt-in for reconfig after upgrade

## **Contributing**

- Open an issue or submit a pull request on GitHub.
- Ensure code adheres to **PEP8 standards** (autoformatted with Black).
- Test changes on a cloud instance before submitting.

---

## **License**

**RLC Cloud Repos** is licensed under the **Apache 2.0 License**.

---

## **Authors**

**CIQ Solutions Delivery Engineering Team**  
[https://github.com/ctrliq/rlc-cloud-repos](https://github.com/ctrliq/rlc-cloud-repos)