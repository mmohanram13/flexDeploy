# Gating Factors Refactoring

## Overview
This refactoring changes the gating factors from being per-ring to being default values that are copied to each deployment when it's created.

## Changes Made

### Database Schema
1. **Removed gating factors from `rings` table**: The columns `avg_cpu_usage_max`, `avg_memory_usage_max`, `avg_disk_free_space_min`, `risk_score_min`, and `risk_score_max` have been removed from the rings table.

2. **Added `default_gating_factors` table**: Stores the default gating factors that will be used as a template for new deployments.
   - `avg_cpu_usage_max`: Maximum average CPU usage threshold
   - `avg_memory_usage_max`: Maximum average memory usage threshold
   - `avg_disk_free_space_min`: Minimum average disk free space threshold
   - `risk_score_min`: Minimum risk score
   - `risk_score_max`: Maximum risk score

3. **Added `deployment_gating_factors` table**: Stores gating factors specific to each deployment (copied from defaults on creation).

### API Changes

#### New Endpoints
- `GET /api/gating-factors` - Get default gating factors
- `PUT /api/gating-factors` - Update default gating factors
- `POST /api/deployments` - Create a new deployment (automatically copies default gating factors)

#### Modified Endpoints
- `GET /api/rings` - No longer returns gating factors
- `PUT /api/rings/{ring_id}` - No longer accepts gating factors
- `GET /api/deployments/{deployment_id}` - Now includes deployment-specific gating factors

### UI Changes

#### Rings Page
- Removed per-ring gating factors section
- Added a single "Default Gating Factors" section at the top
- These default values will be applied to all new deployments

#### Deployment Detail Page
- Added "Gating Factors" section showing the deployment-specific gating factors
- Displays the gating factors that were copied from defaults when the deployment was created

## Migration

### Running the Migration Script
To migrate an existing database:

```bash
cd /Users/mohan-10180/Documents/project-l/flexDeploy
python -m server.migrate_gating_factors
```

The migration script will:
1. Create a backup of your existing database
2. Create the new tables (`default_gating_factors` and `deployment_gating_factors`)
3. Copy Ring 0's gating factors as the default values
4. Copy default gating factors to all existing deployments
5. Remove gating factor columns from the rings table

### Starting Fresh
If you don't have existing data to preserve, you can simply reset the database:

```bash
cd /Users/mohan-10180/Documents/project-l/flexDeploy
python -m server.database
```

This will create a fresh database with the new schema.

## Benefits

1. **Simplified Configuration**: Only one set of gating factors to manage instead of separate ones for each ring
2. **Deployment Isolation**: Each deployment has its own copy of gating factors, allowing for historical tracking
3. **Flexibility**: Gating factors can be changed without affecting existing deployments
4. **Consistency**: All deployments start with the same gating factor baseline

## Usage

### Setting Default Gating Factors
1. Navigate to the Rings page
2. Update the values in the "Default Gating Factors" section
3. Click "Apply" to save

### Viewing Deployment Gating Factors
1. Navigate to Deployments page
2. Click "View Details" on any deployment
3. The "Gating Factors" section shows the values that were copied when the deployment was created

### Creating New Deployments
When a new deployment is created (via the API), the current default gating factors are automatically copied to the deployment's gating factors table.
