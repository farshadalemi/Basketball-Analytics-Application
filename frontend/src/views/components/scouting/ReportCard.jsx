import React from 'react';
import PropTypes from 'prop-types';
import {
  Box,
  Card,
  CardContent,
  CardActions,
  Typography,
  Button,
  Chip,
  IconButton,
  Menu,
  MenuItem,
  ListItemIcon,
  ListItemText,
  Divider
} from '@mui/material';
import {
  Description as ReportIcon,
  MoreVert as MoreIcon,
  Download as DownloadIcon,
  Delete as DeleteIcon,
  Visibility as ViewIcon
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { useToast } from '../../../context/ToastContext';
import { deleteReport } from '../../../controllers/scoutingController';

/**
 * Format date string
 * @param {string} dateString - ISO date string
 * @returns {string} Formatted date
 */
const formatDate = (dateString) => {
  if (!dateString) return 'N/A';
  const date = new Date(dateString);
  return date.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric'
  });
};

/**
 * Get status color
 * @param {string} status - Report status
 * @returns {string} Color for the status chip
 */
const getStatusColor = (status) => {
  switch (status) {
    case 'completed':
      return 'success';
    case 'processing':
      return 'warning';
    case 'queued':
      return 'info';
    case 'failed':
      return 'error';
    default:
      return 'default';
  }
};

/**
 * Report card component
 * @param {Object} props - Component props
 * @param {Object} props.report - Report data
 * @param {Function} props.onRefresh - Refresh callback
 */
const ReportCard = ({ report, onRefresh }) => {
  const navigate = useNavigate();
  const { showSuccess, showError } = useToast();
  const [anchorEl, setAnchorEl] = React.useState(null);
  const open = Boolean(anchorEl);

  const handleClick = (event) => {
    event.stopPropagation();
    setAnchorEl(event.currentTarget);
  };

  const handleClose = (event) => {
    if (event) event.stopPropagation();
    setAnchorEl(null);
  };

  const handleDelete = async (event) => {
    event.stopPropagation();
    setAnchorEl(null);
    
    try {
      await deleteReport(
        report.id,
        () => {
          showSuccess('Report deleted successfully');
          if (onRefresh) onRefresh();
        },
        (error) => showError(error)
      );
    } catch (error) {
      console.error('Error deleting report:', error);
      showError('Failed to delete report');
    }
  };

  const handleView = () => {
    navigate(`/scouting/reports/${report.id}`);
  };

  const handleDownload = () => {
    if (report.download_url) {
      window.open(`${process.env.REACT_APP_SCOUTING_API_URL}${report.download_url}`, '_blank');
    } else {
      showError('Download not available yet');
    }
  };

  return (
    <Card
      sx={{
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        transition: 'transform 0.2s, box-shadow 0.2s',
        '&:hover': {
          transform: 'translateY(-4px)',
          boxShadow: 4
        }
      }}
    >
      <CardContent sx={{ flexGrow: 1 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
          <Typography variant="h6" component="div" noWrap>
            {report.title}
          </Typography>
          <IconButton
            aria-label="more"
            id={`report-menu-button-${report.id}`}
            aria-controls={open ? `report-menu-${report.id}` : undefined}
            aria-expanded={open ? 'true' : undefined}
            aria-haspopup="true"
            onClick={handleClick}
            size="small"
          >
            <MoreIcon />
          </IconButton>
        </Box>
        
        <Chip
          label={report.status}
          color={getStatusColor(report.status)}
          size="small"
          sx={{ mb: 2 }}
        />
        
        <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
          {report.description || 'No description'}
        </Typography>
        
        <Divider sx={{ my: 1 }} />
        
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.5 }}>
          <Typography variant="body2" color="text.secondary">
            <strong>Video:</strong> {report.video_title || 'Unknown'}
          </Typography>
          
          <Typography variant="body2" color="text.secondary">
            <strong>Team:</strong> {report.team_name || 'Not specified'}
          </Typography>
          
          <Typography variant="body2" color="text.secondary">
            <strong>Created:</strong> {formatDate(report.created_at)}
          </Typography>
          
          {report.completed_at && (
            <Typography variant="body2" color="text.secondary">
              <strong>Completed:</strong> {formatDate(report.completed_at)}
            </Typography>
          )}
        </Box>
      </CardContent>
      
      <CardActions sx={{ justifyContent: 'space-between', px: 2, pb: 2 }}>
        <Button
          variant="outlined"
          size="small"
          startIcon={<ViewIcon />}
          onClick={handleView}
        >
          View
        </Button>
        
        <Button
          variant="contained"
          size="small"
          startIcon={<DownloadIcon />}
          onClick={handleDownload}
          disabled={report.status !== 'completed' || !report.download_url}
        >
          Download
        </Button>
      </CardActions>
      
      <Menu
        id={`report-menu-${report.id}`}
        anchorEl={anchorEl}
        open={open}
        onClose={handleClose}
        onClick={handleClose}
        transformOrigin={{ horizontal: 'right', vertical: 'top' }}
        anchorOrigin={{ horizontal: 'right', vertical: 'bottom' }}
      >
        <MenuItem onClick={handleView}>
          <ListItemIcon>
            <ViewIcon fontSize="small" />
          </ListItemIcon>
          <ListItemText>View Details</ListItemText>
        </MenuItem>
        
        <MenuItem
          onClick={handleDownload}
          disabled={report.status !== 'completed' || !report.download_url}
        >
          <ListItemIcon>
            <DownloadIcon fontSize="small" />
          </ListItemIcon>
          <ListItemText>Download PDF</ListItemText>
        </MenuItem>
        
        <Divider />
        
        <MenuItem onClick={handleDelete}>
          <ListItemIcon>
            <DeleteIcon fontSize="small" color="error" />
          </ListItemIcon>
          <ListItemText>Delete</ListItemText>
        </MenuItem>
      </Menu>
    </Card>
  );
};

ReportCard.propTypes = {
  report: PropTypes.object.isRequired,
  onRefresh: PropTypes.func
};

export default ReportCard;
