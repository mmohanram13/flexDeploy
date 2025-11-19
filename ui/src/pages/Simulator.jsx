import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { apiClient } from '../api/client';

// PrimeReact Components
import { Card } from 'primereact/card';
import { Button } from 'primereact/button';
import { Dropdown } from 'primereact/dropdown';
import { InputNumber } from 'primereact/inputnumber';
import { DataTable } from 'primereact/datatable';
import { Column } from 'primereact/column';
import { Toast } from 'primereact/toast';
import { Tag } from 'primereact/tag';
import { Divider } from 'primereact/divider';
import { ProgressBar } from 'primereact/progressbar';
import { Dialog } from 'primereact/dialog';

// PrimeReact Styles
import 'primereact/resources/themes/lara-light-indigo/theme.css';
import 'primereact/resources/primereact.min.css';
import 'primeicons/primeicons.css';

// Custom minimal styles
import '../styles/simulator.css';

export default function Simulator() {
  const navigate = useNavigate();
  const toast = useRef(null);
  const [deployments, setDeployments] = useState([]);
  const [selectedDeployment, setSelectedDeployment] = useState(null);
  const [selectedRing, setSelectedRing] = useState(null);
  const [selectedTarget, setSelectedTarget] = useState(null);
  const [stressLevel, setStressLevel] = useState('normal');
  const [deviceCount, setDeviceCount] = useState(10);
  const [ringDevices, setRingDevices] = useState([]);
  const [targetDevices, setTargetDevices] = useState([]);
  const [loading, setLoading] = useState(false);
  const [showDevicesDialog, setShowDevicesDialog] = useState(false);
  const [dialogSource, setDialogSource] = useState(null); // 'target' or 'ring'

  const rings = [
    { id: 0, name: 'Ring 0: Canary', badge: 'TEST', color: '#00897B' },
    { id: 1, name: 'Ring 1: Low Risk', badge: 'SAFE', color: '#43A047' },
    { id: 2, name: 'Ring 2: High Risk', badge: 'WARN', color: '#FB8C00' },
    { id: 3, name: 'Ring 3: VIP', badge: 'VIP', color: '#E53935' },
  ];

  const targetOptions = [
    { value: 'all', label: 'All Rings', type: 'all' },
    ...rings.map(ring => ({ value: ring.id, label: ring.name, type: 'ring', color: ring.color, badge: ring.badge }))
  ];

  const stressProfiles = [
    { 
      level: 'low', 
      label: 'Light Load', 
      cpu: 25, 
      memory: 30, 
      disk: 20,
      severity: 'success',
      color: '#43A047'
    },
    { 
      level: 'normal', 
      label: 'Normal Load', 
      cpu: 50, 
      memory: 55, 
      disk: 45,
      severity: 'info',
      color: '#1E88E5'
    },
    { 
      level: 'high', 
      label: 'Heavy Load', 
      cpu: 75, 
      memory: 80, 
      disk: 70,
      severity: 'warning',
      color: '#FB8C00'
    },
    { 
      level: 'critical', 
      label: 'Critical Load', 
      cpu: 95, 
      memory: 92, 
      disk: 88,
      severity: 'danger',
      color: '#E53935'
    },
  ];

  const statusOptions = [
    'Not Started',
    'In Progress',
    'Completed',
    'Failed',
    'Stopped',
  ];

  useEffect(() => {
    fetchDeployments();
  }, []);

  useEffect(() => {
    if (selectedTarget !== null) {
      fetchTargetDevices();
    }
  }, [selectedTarget]);

  useEffect(() => {
    if (selectedRing !== null && selectedDeployment) {
      fetchRingDevices();
    }
  }, [selectedRing, selectedDeployment]);

  const fetchDeployments = async () => {
    try {
      const data = await apiClient.getDeployments();
      setDeployments(data.map(d => ({ label: `${d.deploymentName} (${d.deploymentId})`, value: d.deploymentId })));
      if (data.length > 0) {
        setSelectedDeployment(data[0].deploymentId);
      }
    } catch (error) {
      console.error('Error fetching deployments:', error);
      showToast('error', 'Error', 'Failed to load deployments');
    }
  };

  const fetchRingDevices = async () => {
    if (!selectedDeployment || selectedRing === null) return;
    
    setLoading(true);
    try {
      const data = await apiClient.getRingDevices(selectedDeployment, selectedRing.id);
      setRingDevices(data.devices || []);
    } catch (error) {
      console.error('Error fetching ring devices:', error);
      setRingDevices([]);
    } finally {
      setLoading(false);
    }
  };

  const fetchTargetDevices = async () => {
    if (!selectedDeployment || selectedTarget === null) return;
    
    setLoading(true);
    try {
      if (selectedTarget.type === 'all') {
        // Fetch devices from all rings
        const allDevices = [];
        for (const ring of rings) {
          const data = await apiClient.getRingDevices(selectedDeployment, ring.id);
          allDevices.push(...(data.devices || []));
        }
        setTargetDevices(allDevices);
      } else {
        // Fetch devices from specific ring
        const data = await apiClient.getRingDevices(selectedDeployment, selectedTarget.value);
        setTargetDevices(data.devices || []);
      }
    } catch (error) {
      console.error('Error fetching target devices:', error);
      setTargetDevices([]);
    } finally {
      setLoading(false);
    }
  };

  const showToast = (severity, summary, detail) => {
    toast.current.show({ severity, summary, detail, life: 3000 });
  };

  const handlePopulateDemoDeployments = async () => {
    setLoading(true);
    try {
      const demoDeployments = [
        { deploymentId: 'DEP-001', deploymentName: 'Windows 11 Update' },
        { deploymentId: 'DEP-002', deploymentName: 'Security Patch Q4 2025' },
        { deploymentId: 'DEP-003', deploymentName: 'Microsoft Office 365 Update' },
        { deploymentId: 'DEP-004', deploymentName: 'Test Deployment' },
      ];

      for (const deployment of demoDeployments) {
        await apiClient.createDeployment(deployment);
      }

      showToast('success', 'Success', `Created ${demoDeployments.length} demo deployments`);
      await fetchDeployments();
    } catch (error) {
      console.error('Error populating deployments:', error);
      showToast('error', 'Error', 'Failed to populate deployments');
    } finally {
      setLoading(false);
    }
  };

  const handlePopulateDevices = async () => {
    if (!deviceCount || deviceCount < 1) {
      showToast('warn', 'Warning', 'Enter a valid device count');
      return;
    }

    setLoading(true);
    try {
      const manufacturers = ['Dell', 'HP', 'Lenovo', 'Apple', 'Microsoft'];
      const models = ['Latitude', 'EliteBook', 'ThinkPad', 'MacBook Pro', 'Surface'];
      const osNames = ['Windows 10', 'Windows 11', 'macOS', 'Ubuntu'];
      const sites = ['New York', 'San Francisco', 'London', 'Tokyo', 'Sydney'];
      const departments = ['Engineering', 'Sales', 'Marketing', 'HR', 'Finance'];

      let createdCount = 0;
      
      for (let i = 0; i < deviceCount; i++) {
        const deviceId = `DEV-${Date.now()}-${i}`;
        const deviceData = {
          deviceId: deviceId,
          deviceName: `Device ${deviceId}`,
          manufacturer: manufacturers[Math.floor(Math.random() * manufacturers.length)],
          model: models[Math.floor(Math.random() * models.length)],
          osName: osNames[Math.floor(Math.random() * osNames.length)],
          site: sites[Math.floor(Math.random() * sites.length)],
          department: departments[Math.floor(Math.random() * departments.length)],
          totalMemory: Math.floor(Math.random() * 16 + 8) * 1024, // 8-24 GB
          totalStorage: Math.floor(Math.random() * 512 + 256) * 1024, // 256-768 GB
          networkSpeed: Math.floor(Math.random() * 900 + 100), // 100-1000 Mbps
          avgCpuUsage: Math.random() * 30 + 20, // 20-50%
          avgMemoryUsage: Math.random() * 30 + 30, // 30-60%
          avgDiskSpace: Math.random() * 30 + 30, // 30-60%
        };

        await apiClient.createDevice(deviceData);
        createdCount++;
      }

      showToast('success', 'Success', `Created ${createdCount} devices`);
      fetchRingDevices();
    } catch (error) {
      console.error('Error populating devices:', error);
      showToast('error', 'Error', 'Failed to populate devices');
    } finally {
      setLoading(false);
    }
  };

  const handleApplyStressToRing = async () => {
    if (selectedTarget === null) {
      showToast('warn', 'Warning', 'Please select a target');
      return;
    }

    if (targetDevices.length === 0) {
      showToast('warn', 'Warning', 'No devices in the selected target');
      return;
    }

    setLoading(true);
    try {
      const profile = stressProfiles.find(p => p.level === stressLevel);
      
      // Update all devices in the target
      for (const device of targetDevices) {
        await apiClient.updateDeviceMetrics({
          deviceId: device.deviceId,
          avgCpuUsage: profile.cpu + (Math.random() * 10 - 5), // ±5% variance
          avgMemoryUsage: profile.memory + (Math.random() * 10 - 5),
          avgDiskSpace: profile.disk + (Math.random() * 10 - 5),
        });
      }

      const targetName = selectedTarget.type === 'all' ? 'All Rings' : selectedTarget.label;
      showToast('success', 'Success', `Applied ${profile.label} to ${targetDevices.length} devices in ${targetName}`);
      fetchTargetDevices();
      if (selectedRing !== null) {
        fetchRingDevices();
      }
    } catch (error) {
      console.error('Error applying stress:', error);
      showToast('error', 'Error', 'Failed to apply stress');
    } finally {
      setLoading(false);
    }
  };

  const handleUpdateRingStatus = async (status) => {
    if (!selectedDeployment || selectedRing === null) {
      showToast('warn', 'Warning', 'Select deployment and ring');
      return;
    }

    try {
      await apiClient.updateDeploymentRingStatus({
        deploymentId: selectedDeployment,
        ringId: selectedRing.id,
        status: status,
      });
      showToast('success', 'Success', `Status updated to ${status}`);
    } catch (error) {
      console.error('Error updating status:', error);
      showToast('error', 'Error', 'Failed to update status');
    }
  };

  const riskScoreTemplate = (rowData) => {
    const score = rowData.riskScore;
    let severity = 'danger';
    if (score >= 70) severity = 'success';
    else if (score >= 31) severity = 'warning';
    
    return <Tag value={score} severity={severity} />;
  };

  const metricTemplate = (value) => {
    return `${value.toFixed(1)}%`;
  };

  return (
    <div className="simulator-container">
      <Toast ref={toast} />
      
      {/* Header */}
      <div className="simulator-header">
        <div className="header-content">
          <div className="header-left">
            <i className="pi pi-flask header-icon"></i>
            <div>
              <h1 className="header-title">FlexDeploy Simulator</h1>
            </div>
          </div>
          <Button
            label="Go To Application"
            icon="pi pi-arrow-left"
            className="p-button-outlined header-button"
            onClick={() => navigate('/')}
          />
        </div>
      </div>

      {/* Main Content */}
      <div className="simulator-content">
        
        {/* Device Population Section */}
        <Card className="section-card">
          <div className="section-header">
            <h2 className="section-title">
              <i className="pi pi-plus-circle section-icon"></i>
              Setup & Management
            </h2>
          </div>

          <div className="device-management">
            <div className="device-populate">
              <div className="populate-info">
                <p className="info-text">Create demo deployments and test devices to simulate deployment scenarios. Devices will be automatically categorized into rings based on ring configuration.</p>
              </div>
              <div className="setup-actions">
                <div className="setup-action-item">
                  <label className="setup-action-label">Create Test Devices</label>
                  <div className="device-create-group">
                    <div className="device-count-field">
                      <label className="form-label">Number of Devices</label>
                      <InputNumber
                        value={deviceCount}
                        onValueChange={(e) => setDeviceCount(e.value)}
                        min={1}
                        max={100}
                        placeholder="Enter count"
                        className="device-input"
                      />
                    </div>
                    <Button
                      label="Populate Devices"
                      icon="pi pi-plus"
                      className="p-button-lg setup-action-btn"
                      onClick={handlePopulateDevices}
                      loading={loading}
                    />
                  </div>
                </div>
                <div className="setup-divider"></div>
                <div className="setup-action-item">
                  <label className="setup-action-label">Create Demo Data</label>
                  <Button
                    label="Populate Demo Deployments"
                    icon="pi pi-folder-plus"
                    className="p-button-lg setup-action-btn"
                    onClick={handlePopulateDemoDeployments}
                    loading={loading}
                  />
                </div>
              </div>
            </div>
          </div>
        </Card>

        {/* Stress Profiles */}
        <Card className="section-card">
          <div className="section-header">
            <div>
              <h2 className="section-title">
                <i className="pi pi-bolt section-icon"></i>
                Simulate Load
              </h2>
              <p className="section-description">
                Select a target and stress profile to update device metrics
              </p>
            </div>
          </div>

          {/* Target Selector */}
          <div className="target-selector-container">
            <div className="config-item">
              <div className="config-item-header">
                <label className="config-label">Target Scope</label>
                <div className="config-actions">
                  <Button
                    icon="pi pi-refresh"
                    className="p-button-text p-button-sm refresh-btn"
                    onClick={fetchTargetDevices}
                    tooltip="Reload target devices"
                    tooltipOptions={{ position: 'top' }}
                    disabled={!selectedTarget}
                  />
                  <Button
                    icon="pi pi-eye"
                    label="View Devices"
                    className="p-button-sm view-devices-btn"
                    onClick={() => {
                      setDialogSource('target');
                      setShowDevicesDialog(true);
                    }}
                    disabled={!selectedTarget || targetDevices.length === 0}
                    tooltip="View devices in target"
                    tooltipOptions={{ position: 'top' }}
                  />
                </div>
              </div>
              <Dropdown
                value={selectedTarget}
                options={targetOptions}
                onChange={(e) => setSelectedTarget(e.value)}
                optionLabel="label"
                placeholder="Select a target scope"
                className="w-full"
                itemTemplate={(option) => (
                  <div className="ring-option">
                    {option.type === 'all' ? (
                      <>
                        <i className="pi pi-globe" style={{ color: 'var(--primary-blue)', fontSize: '1.1rem' }}></i>
                        <span>All Rings</span>
                      </>
                    ) : (
                      <>
                        <span className="ring-badge" style={{ backgroundColor: option.color }}>
                          {option.badge}
                        </span>
                        <span>{option.label}</span>
                      </>
                    )}
                  </div>
                )}
                valueTemplate={(option, props) => {
                  if (option) {
                    return (
                      <div className="ring-option">
                        {option.type === 'all' ? (
                          <>
                            <i className="pi pi-globe" style={{ color: 'var(--primary-blue)', fontSize: '1.1rem' }}></i>
                            <span>All Rings</span>
                          </>
                        ) : (
                          <>
                            <span className="ring-badge" style={{ backgroundColor: option.color }}>
                              {option.badge}
                            </span>
                            <span>{option.label}</span>
                          </>
                        )}
                      </div>
                    );
                  }
                  return <span className="text-grey-500">{props.placeholder}</span>;
                }}
              />
              {selectedTarget && (
                <div className="device-count-info">
                  <i className="pi pi-desktop"></i>
                  <span className="device-count-text">{targetDevices.length} devices</span>
                </div>
              )}
            </div>
          </div>
          
          <div className="stress-grid">
            {stressProfiles.map((profile) => (
              <div
                key={profile.level}
                className={`stress-card ${stressLevel === profile.level ? 'stress-card-active' : ''}`}
                onClick={() => setStressLevel(profile.level)}
              >
                <div className="stress-header">
                  <Tag value={profile.label} severity={profile.severity} />
                </div>
                <div className="stress-metrics">
                  <div className="metric-row">
                    <span className="metric-label">CPU</span>
                    <span className="metric-value">{profile.cpu}%</span>
                  </div>
                  <Divider />
                  <div className="metric-row">
                    <span className="metric-label">Memory</span>
                    <span className="metric-value">{profile.memory}%</span>
                  </div>
                  <Divider />
                  <div className="metric-row">
                    <span className="metric-label">Disk</span>
                    <span className="metric-value">{profile.disk}%</span>
                  </div>
                </div>
              </div>
            ))}
          </div>

          <Button
            label={`Apply ${stressLevel.charAt(0).toUpperCase() + stressLevel.slice(1)} Load to ${selectedTarget?.type === 'all' ? 'All Rings' : (selectedTarget?.label || 'Target')}`}
            icon="pi pi-play"
            className="p-button-lg apply-button w-full mt-4"
            onClick={handleApplyStressToRing}
            loading={loading}
            disabled={!selectedTarget || targetDevices.length === 0}
          />
        </Card>

        {/* Devices Dialog */}
        <Dialog
          header={
            dialogSource === 'ring' && selectedRing
              ? `Devices in ${selectedRing.name}` 
              : dialogSource === 'target' && selectedTarget
                ? `Devices in ${selectedTarget.label}` 
                : 'Devices'
          }
          visible={showDevicesDialog}
          onHide={() => {
            setShowDevicesDialog(false);
            setDialogSource(null);
          }}
          style={{ width: '90vw', maxWidth: '1200px' }}
          modal
        >
          <DataTable
            value={dialogSource === 'ring' ? ringDevices : targetDevices}
            stripedRows
            className="devices-table"
            paginator
            rows={10}
            emptyMessage="No devices found"
            sortMode="multiple"
            removableSort
          >
            <Column field="deviceId" header="Device ID" sortable style={{ minWidth: '150px' }} />
            <Column field="deviceName" header="Name" sortable style={{ minWidth: '150px' }} />
            <Column field="manufacturer" header="Manufacturer" sortable style={{ minWidth: '120px' }} />
            <Column field="model" header="Model" sortable style={{ minWidth: '120px' }} />
            <Column
              field="avgCpuUsage"
              header="CPU Usage"
              body={(row) => metricTemplate(row.avgCpuUsage)}
              sortable
              style={{ minWidth: '120px' }}
            />
            <Column
              field="avgMemoryUsage"
              header="Memory Usage"
              body={(row) => metricTemplate(row.avgMemoryUsage)}
              sortable
              style={{ minWidth: '130px' }}
            />
            <Column
              field="avgDiskSpace"
              header="Disk Usage"
              body={(row) => metricTemplate(row.avgDiskSpace)}
              sortable
              style={{ minWidth: '120px' }}
            />
            <Column
              field="riskScore"
              header="Risk Score"
              body={riskScoreTemplate}
              sortable
              style={{ minWidth: '120px' }}
            />
          </DataTable>
        </Dialog>

        {/* Configuration */}
        <Card className="section-card">
          <div className="section-header">
            <div>
              <h2 className="section-title">
                <i className="pi pi-cog section-icon"></i>
                Deployment Status Control
              </h2>
              <p className="section-description">
                Select deployment and ring, then update status
              </p>
            </div>
          </div>

          <div className="config-grid">
            <div className="config-item">
              <div className="config-item-header">
                <label className="config-label">Deployment</label>
                <Button
                  icon="pi pi-refresh"
                  className="p-button-text p-button-sm refresh-btn"
                  onClick={fetchDeployments}
                  tooltip="Reload deployments"
                  tooltipOptions={{ position: 'top' }}
                />
              </div>
              <Dropdown
                value={selectedDeployment}
                options={deployments}
                onChange={(e) => setSelectedDeployment(e.value)}
                placeholder="Select deployment"
                className="w-full"
              />
            </div>

            <div className="config-item">
              <div className="config-item-header">
                <label className="config-label">Target Ring</label>
                <div className="config-actions">
                  <Button
                    icon="pi pi-refresh"
                    className="p-button-text p-button-sm refresh-btn"
                    onClick={fetchRingDevices}
                    tooltip="Reload ring devices"
                    tooltipOptions={{ position: 'top' }}
                  />
                  <Button
                    icon="pi pi-eye"
                    label="View Devices"
                    className="p-button-sm view-devices-btn"
                    onClick={() => {
                      setDialogSource('ring');
                      setShowDevicesDialog(true);
                    }}
                    disabled={!selectedRing || ringDevices.length === 0}
                    tooltip="View devices in ring"
                    tooltipOptions={{ position: 'top' }}
                  />
                </div>
              </div>
              <Dropdown
                value={selectedRing}
                options={rings}
                onChange={(e) => setSelectedRing(e.value)}
                optionLabel="name"
                placeholder="Select ring"
                className="w-full"
                itemTemplate={(option) => (
                  <div className="ring-option">
                    <span className="ring-badge" style={{ backgroundColor: option.color }}>
                      {option.badge}
                    </span>
                    <span>{option.name}</span>
                  </div>
                )}
                valueTemplate={(option) => option ? (
                  <div className="ring-option">
                    <span className="ring-badge" style={{ backgroundColor: option.color }}>
                      {option.badge}
                    </span>
                    <span>{option.name}</span>
                  </div>
                ) : 'Select ring'}
              />
              {selectedRing && (
                <div className="device-count-info">
                  <i className="pi pi-desktop"></i>
                  <span className="device-count-text">{ringDevices.length} devices</span>
                </div>
              )}
            </div>
          </div>

          <Divider />

          <div className="status-section">
            <label className="config-label">Update Status</label>
            <div className="status-grid">
              {statusOptions.map((status) => (
                <Button
                  key={status}
                  label={status}
                  className="p-button-outlined status-button"
                  onClick={() => handleUpdateRingStatus(status)}
                  disabled={!selectedDeployment || !selectedRing}
                />
              ))}
            </div>
          </div>
        </Card>

        {/* Loading Bar */}
        {loading && <ProgressBar mode="indeterminate" className="loading-bar" />}
      </div>
    </div>
  );
}
