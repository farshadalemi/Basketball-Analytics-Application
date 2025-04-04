import React from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Card,
  CardContent,
  CardMedia,
  Typography,
  CardActionArea,
  Box,
  Chip,
  IconButton,
  Menu,
  MenuItem,
  ListItemIcon,
  ListItemText
} from '@mui/material';
import {
  MoreVert as MoreIcon,
  Delete as DeleteIcon,
  Edit as EditIcon,
  Share as ShareIcon,
  PlayArrow as PlayIcon,
  Folder as FolderIcon,
  Label as LabelIcon
} from '@mui/icons-material';
import { formatDuration, getVideoStatusText } from '../../../models/video';

/**
 * Video card component for displaying video thumbnails
 * @param {Object} props - Component props
 * @param {Object} props.video - Video data
 * @param {Function} props.onDelete - Delete callback
 */
const VideoCard = ({ video, onDelete }) => {
  const navigate = useNavigate();
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

  const handleDelete = (event) => {
    event.stopPropagation();
    setAnchorEl(null);
    if (onDelete) onDelete(video.id);
  };

  const handleCardClick = () => {
    navigate(`/videos/${video.id}`);
  };

  // Format date
  const formatDate = (dateString) => {
    if (!dateString) return 'Unknown date';
    const date = new Date(dateString);
    return date.toLocaleDateString();
  };

  // Get status color
  const getStatusColor = (status) => {
    switch (status) {
      case 'completed':
        return 'success';
      case 'processing':
        return 'warning';
      case 'failed':
        return 'error';
      default:
        return 'default';
    }
  };

  return (
    <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column', position: 'relative' }}>
      {/* Menu button - moved outside CardActionArea */}
      <IconButton
        aria-label="more"
        id={`video-menu-${video.id}`}
        aria-controls={open ? `video-menu-${video.id}` : undefined}
        aria-expanded={open ? 'true' : undefined}
        aria-haspopup="true"
        onClick={handleClick}
        size="small"
        sx={{ position: 'absolute', top: 8, right: 8, zIndex: 2, bgcolor: 'rgba(255,255,255,0.7)' }}
      >
        <MoreIcon />
      </IconButton>

      <CardActionArea onClick={handleCardClick}>
        <Box sx={{ position: 'relative' }}>
          <CardMedia
            component="img"
            height="140"
            image={'/video-placeholder.svg'}
            alt={video.title}
            sx={{
              objectFit: 'cover',
              backgroundColor: 'rgba(0, 0, 0, 0.08)'
            }}
            onError={(e) => {
              console.log('Thumbnail failed to load:', video.thumbnail_url);
              // If thumbnail fails to load, use a placeholder
              e.target.src = '/video-placeholder.svg';
            }}
          />

          {/* Duration badge */}
          {video.duration > 0 && (
            <Box
              sx={{
                position: 'absolute',
                bottom: 8,
                right: 8,
                bgcolor: 'rgba(0, 0, 0, 0.7)',
                color: 'white',
                px: 0.8,
                py: 0.2,
                borderRadius: 1,
                fontSize: '0.75rem'
              }}
            >
              {formatDuration(video.duration)}
            </Box>
          )}

          {/* Play button overlay */}
          <Box
            sx={{
              position: 'absolute',
              top: 0,
              left: 0,
              right: 0,
              bottom: 0,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              opacity: 0,
              transition: 'opacity 0.2s',
              '&:hover': {
                opacity: 1,
                bgcolor: 'rgba(0, 0, 0, 0.3)'
              }
            }}
          >
            <PlayIcon sx={{ fontSize: 48, color: 'white' }} />
          </Box>
        </Box>

        <CardContent sx={{ flexGrow: 1 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
            {/* Title with color indicator if present */}
            <Box sx={{ display: 'flex', alignItems: 'center', width: '100%' }}>
              {video.color && (
                <Box
                  sx={{
                    width: 12,
                    height: 12,
                    borderRadius: '50%',
                    bgcolor: video.color,
                    mr: 1,
                    flexShrink: 0
                  }}
                />
              )}
              <Typography gutterBottom variant="h6" component="div" noWrap>
                {video.title}
              </Typography>
            </Box>
          </Box>

          <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
            {video.description || 'No description'}
          </Typography>

          {/* Folder */}
          {video.folder && video.folder !== 'Uncategorized' && (
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
              <FolderIcon sx={{ fontSize: '0.875rem', mr: 0.5, color: 'text.secondary' }} />
              <Typography variant="caption" color="text.secondary">
                {video.folder}
              </Typography>
            </Box>
          )}

          {/* Tags */}
          {video.tags && video.tags.length > 0 && (
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5, mb: 1 }}>
              {video.tags.map(tag => (
                <Chip
                  key={tag}
                  label={tag}
                  size="small"
                  variant="outlined"
                  sx={{ height: 20, '& .MuiChip-label': { px: 1, py: 0.25, fontSize: '0.625rem' } }}
                />
              ))}
            </Box>
          )}

          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mt: 1 }}>
            <Typography variant="caption" color="text.secondary">
              {formatDate(video.createdAt)}
            </Typography>

            <Chip
              label={getVideoStatusText(video)}
              size="small"
              color={getStatusColor(video.processingStatus)}
              variant="outlined"
            />
          </Box>
        </CardContent>
      </CardActionArea>

      {/* Menu */}
      <Menu
        id={`video-menu-${video.id}`}
        anchorEl={anchorEl}
        open={open}
        onClose={handleClose}
        onClick={handleClose}
        transformOrigin={{ horizontal: 'right', vertical: 'top' }}
        anchorOrigin={{ horizontal: 'right', vertical: 'bottom' }}
      >
        <MenuItem onClick={handleCardClick}>
          <ListItemIcon>
            <PlayIcon fontSize="small" />
          </ListItemIcon>
          <ListItemText>Play</ListItemText>
        </MenuItem>
        <MenuItem disabled>
          <ListItemIcon>
            <EditIcon fontSize="small" />
          </ListItemIcon>
          <ListItemText>Edit</ListItemText>
        </MenuItem>
        <MenuItem disabled>
          <ListItemIcon>
            <ShareIcon fontSize="small" />
          </ListItemIcon>
          <ListItemText>Share</ListItemText>
        </MenuItem>
        <MenuItem onClick={handleDelete}>
          <ListItemIcon>
            <DeleteIcon fontSize="small" color="error" />
          </ListItemIcon>
          <ListItemText sx={{ color: 'error.main' }}>Delete</ListItemText>
        </MenuItem>
      </Menu>
    </Card>
  );
};

export default VideoCard;
