Name:           rlc-cloud-repos
Version:        0.1.0
Release:        1%{?dist}
Summary:        Cloud-aware repo autoconfiguration

License:        MIT
URL:            https://ciq.com/
Source0:        %{name}-%{version}.tar.gz

BuildArch:      noarch
BuildRequires:  python3-devel
BuildRequires:  python3-pip
BuildRequires:  python3-setuptools
BuildRequires:  python3-build
BuildRequires:  python3-wheel
BuildRequires:  pyproject-rpm-macros

Requires:       python3
Requires:       pyyaml
Requires:       ruamel.yaml

%description
Installs cloud-init-aware repository autoconfiguration for RLC images.
Designed for first-boot automation using cloud metadata and geolocation-based mirror selection.

%prep
%setup -q

%build
%pyproject_wheel

%install
install -d %{buildroot}/%{_bindir}
install -Dm0755 src/rlc_cloud_repos/scripts/rlc-cloud-repos-wrapper.sh %{buildroot}/usr/libexec/rlc-cloud-repos-hook.sh
install -Dm0644 src/rlc_cloud_repos/scripts/99-rlc-cloud-repos.cfg %{buildroot}/etc/cloud/cloud.cfg.d/99-rlc-cloud-repos.cfg
install -Dm0644 src/rlc_cloud_repos/data/ciq-mirrors.yaml %{buildroot}/etc/rlc-cloud-repos/ciq-mirrors.yaml
install -Dm0644 src/rlc_cloud_repos/data/ciq-depot.repo %{buildroot}/etc/rlc-cloud-repos/ciq-depot.repo
%pyproject_install

%files
%{_bindir}/rlc-cloud-repos
%license LICENSE
%doc README.md
%{python3_sitelib}/rlc_cloud_repos
%{python3_sitelib}/rlc_cloud_repos-*.dist-info
%config(noreplace) /etc/rlc-cloud-repos/ciq-mirrors.yaml
%config(noreplace) /etc/rlc-cloud-repos/ciq-depot.repo
%config(noreplace) /etc/cloud/cloud.cfg.d/99-rlc-cloud-repos.cfg
/usr/libexec/rlc-cloud-repos-hook.sh

%changelog
* Mon Mar 31 2025 Joel Hanger <jhanger@ciq.com> - 0.1.0-1
- Initial version of cloud-aware repo autoconfig package
