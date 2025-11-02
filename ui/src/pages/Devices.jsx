import React, { useState, useMemo, useEffect } from 'react';
import {
  Box,
  Typography,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  TextField,
  TableSortLabel,
  CircularProgress,
} from '@mui/material';
import { apiClient } from '../api/client';

export default function Devices() {
  const [loading, setLoading] = useState(true);
  const [devices, setDevices] = useState([]);
  const [orderBy, setOrderBy] = useState('deviceId');
  const [order, setOrder] = useState('asc');
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    const fetchDevices = async () => {
      try {
        const data = await apiClient.getDevices();
        setDevices(data);
      } catch (error) {
        console.error('Error fetching devices:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchDevices();
  }, []);

  const getChipColor = (riskScore) => {
    if (riskScore >= 71) return 'success';
    if (riskScore >= 31) return 'warning';
    return 'error';
  };

  const handleSort = (property) => {
    const isAsc = orderBy === property && order === 'asc';
    setOrder(isAsc ? 'desc' : 'asc');
    setOrderBy(property);
  };

  const getComparator = (order, orderBy) => {
    return order === 'desc'
      ? (a, b) => descendingComparator(a, b, orderBy)
      : (a, b) => -descendingComparator(a, b, orderBy);
  };

  const descendingComparator = (a, b, orderBy) => {
    let aVal = a[orderBy];
    let bVal = b[orderBy];

    // Handle numeric comparisons
    if (typeof aVal === 'number' && typeof bVal === 'number') {
      return bVal - aVal;
    }

    // Handle string comparisons
    if (bVal < aVal) return -1;
    if (bVal > aVal) return 1;
    return 0;
  };

  const filteredAndSortedDevices = useMemo(() => {
    let filtered = devices;

    // Apply search filter
    if (searchQuery) {
      filtered = devices.filter((device) =>
        Object.values(device).some((value) =>
          String(value).toLowerCase().includes(searchQuery.toLowerCase())
        )
      );
    }

    // Apply sorting
    return filtered.slice().sort(getComparator(order, orderBy));
  }, [devices, searchQuery, order, orderBy]);

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Devices
      </Typography>

      <Box sx={{ mb: 2 }}>
        <TextField
          fullWidth
          label="Search devices..."
          variant="outlined"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          size="small"
        />
      </Box>

      <TableContainer component={Paper} elevation={2}>
        <Table sx={{ minWidth: 1800 }}>
          <TableHead>
            <TableRow>
              <TableCell sx={{ fontWeight: 'bold' }}>
                <TableSortLabel
                  active={orderBy === 'deviceId'}
                  direction={orderBy === 'deviceId' ? order : 'asc'}
                  onClick={() => handleSort('deviceId')}
                >
                  Device ID
                </TableSortLabel>
              </TableCell>
              <TableCell sx={{ fontWeight: 'bold' }}>
                <TableSortLabel
                  active={orderBy === 'deviceName'}
                  direction={orderBy === 'deviceName' ? order : 'asc'}
                  onClick={() => handleSort('deviceName')}
                >
                  Device Name
                </TableSortLabel>
              </TableCell>
              <TableCell sx={{ fontWeight: 'bold' }}>
                <TableSortLabel
                  active={orderBy === 'manufacturer'}
                  direction={orderBy === 'manufacturer' ? order : 'asc'}
                  onClick={() => handleSort('manufacturer')}
                >
                  Manufacturer
                </TableSortLabel>
              </TableCell>
              <TableCell sx={{ fontWeight: 'bold' }}>
                <TableSortLabel
                  active={orderBy === 'model'}
                  direction={orderBy === 'model' ? order : 'asc'}
                  onClick={() => handleSort('model')}
                >
                  Model
                </TableSortLabel>
              </TableCell>
              <TableCell sx={{ fontWeight: 'bold' }}>
                <TableSortLabel
                  active={orderBy === 'osName'}
                  direction={orderBy === 'osName' ? order : 'asc'}
                  onClick={() => handleSort('osName')}
                >
                  OS Name
                </TableSortLabel>
              </TableCell>
              <TableCell sx={{ fontWeight: 'bold' }}>
                <TableSortLabel
                  active={orderBy === 'site'}
                  direction={orderBy === 'site' ? order : 'asc'}
                  onClick={() => handleSort('site')}
                >
                  Site
                </TableSortLabel>
              </TableCell>
              <TableCell sx={{ fontWeight: 'bold' }}>
                <TableSortLabel
                  active={orderBy === 'department'}
                  direction={orderBy === 'department' ? order : 'asc'}
                  onClick={() => handleSort('department')}
                >
                  Department
                </TableSortLabel>
              </TableCell>
              <TableCell sx={{ fontWeight: 'bold' }}>
                <TableSortLabel
                  active={orderBy === 'ring'}
                  direction={orderBy === 'ring' ? order : 'asc'}
                  onClick={() => handleSort('ring')}
                >
                  Ring
                </TableSortLabel>
              </TableCell>
              <TableCell sx={{ fontWeight: 'bold' }}>
                <TableSortLabel
                  active={orderBy === 'totalMemory'}
                  direction={orderBy === 'totalMemory' ? order : 'asc'}
                  onClick={() => handleSort('totalMemory')}
                >
                  Total Memory
                </TableSortLabel>
              </TableCell>
              <TableCell sx={{ fontWeight: 'bold' }}>
                <TableSortLabel
                  active={orderBy === 'totalStorage'}
                  direction={orderBy === 'totalStorage' ? order : 'asc'}
                  onClick={() => handleSort('totalStorage')}
                >
                  Total Storage
                </TableSortLabel>
              </TableCell>
              <TableCell sx={{ fontWeight: 'bold' }}>
                <TableSortLabel
                  active={orderBy === 'networkSpeed'}
                  direction={orderBy === 'networkSpeed' ? order : 'asc'}
                  onClick={() => handleSort('networkSpeed')}
                >
                  Network Speed
                </TableSortLabel>
              </TableCell>
              <TableCell sx={{ fontWeight: 'bold' }}>
                <TableSortLabel
                  active={orderBy === 'avgCpuUsage'}
                  direction={orderBy === 'avgCpuUsage' ? order : 'asc'}
                  onClick={() => handleSort('avgCpuUsage')}
                >
                  Average CPU Usage
                </TableSortLabel>
              </TableCell>
              <TableCell sx={{ fontWeight: 'bold' }}>
                <TableSortLabel
                  active={orderBy === 'avgMemoryUsage'}
                  direction={orderBy === 'avgMemoryUsage' ? order : 'asc'}
                  onClick={() => handleSort('avgMemoryUsage')}
                >
                  Average Memory Usage
                </TableSortLabel>
              </TableCell>
              <TableCell sx={{ fontWeight: 'bold' }}>
                <TableSortLabel
                  active={orderBy === 'avgDiskSpace'}
                  direction={orderBy === 'avgDiskSpace' ? order : 'asc'}
                  onClick={() => handleSort('avgDiskSpace')}
                >
                  Average Disk Space
                </TableSortLabel>
              </TableCell>
              <TableCell sx={{ fontWeight: 'bold' }}>
                <TableSortLabel
                  active={orderBy === 'riskScore'}
                  direction={orderBy === 'riskScore' ? order : 'asc'}
                  onClick={() => handleSort('riskScore')}
                >
                  Risk Score
                </TableSortLabel>
              </TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {filteredAndSortedDevices.map((device) => (
              <TableRow key={device.deviceId} hover>
                <TableCell>{device.deviceId}</TableCell>
                <TableCell>{device.deviceName}</TableCell>
                <TableCell>{device.manufacturer}</TableCell>
                <TableCell>{device.model}</TableCell>
                <TableCell>{device.osName}</TableCell>
                <TableCell>{device.site}</TableCell>
                <TableCell>{device.department}</TableCell>
                <TableCell>{device.ring}</TableCell>
                <TableCell>{device.totalMemory}</TableCell>
                <TableCell>{device.totalStorage}</TableCell>
                <TableCell>{device.networkSpeed}</TableCell>
                <TableCell>{device.avgCpuUsage}%</TableCell>
                <TableCell>{device.avgMemoryUsage}%</TableCell>
                <TableCell>{device.avgDiskSpace}%</TableCell>
                <TableCell>
                  <Chip
                    label={device.riskScore}
                    color={getChipColor(device.riskScore)}
                    size="small"
                  />
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </Box>
  );
}
