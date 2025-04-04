import React, { useState, useEffect } from 'react';
import {
  Box,
  TextField,
  Chip,
  Typography,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  IconButton,
  Tooltip,
  useTheme,
  useMediaQuery
} from '@mui/material';
import {
  Add as AddIcon,
  Folder as FolderIcon,
  Label as LabelIcon,
  ColorLens as ColorIcon,
  Close as CloseIcon
} from '@mui/icons-material';

// Predefined color options
const colorOptions = [
  { name: 'Red', value: '#f44336' },
  { name: 'Pink', value: '#e91e63' },
  { name: 'Purple', value: '#9c27b0' },
  { name: 'Deep Purple', value: '#673ab7' },
  { name: 'Indigo', value: '#3f51b5' },
  { name: 'Blue', value: '#2196f3' },
  { name: 'Light Blue', value: '#03a9f4' },
  { name: 'Cyan', value: '#00bcd4' },
  { name: 'Teal', value: '#009688' },
  { name: 'Green', value: '#4caf50' },
  { name: 'Light Green', value: '#8bc34a' },
  { name: 'Lime', value: '#cddc39' },
  { name: 'Yellow', value: '#ffeb3b' },
  { name: 'Amber', value: '#ffc107' },
  { name: 'Orange', value: '#ff9800' },
  { name: 'Deep Orange', value: '#ff5722' },
  { name: 'Brown', value: '#795548' },
  { name: 'Grey', value: '#9e9e9e' },
  { name: 'Blue Grey', value: '#607d8b' }
];

// Predefined folder options (can be expanded)
const folderOptions = [
  'Uncategorized',
  'Favorites',
  'Training',
  'Games',
  'Analysis',
  'Drills',
  'Tactics',
  'Other'
];

/**
 * Component for editing video tags, color, and folder
 */
const VideoTagsEditor = ({ video, onSave, onCancel }) => {
  const [open, setOpen] = useState(false);
  const [tags, setTags] = useState(video.tags || []);
  const [newTag, setNewTag] = useState('');
  const [color, setColor] = useState(video.color || '');
  const [folder, setFolder] = useState(video.folder || 'Uncategorized');
  
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
  
  // Handle dialog open/close
  const handleOpen = () => setOpen(true);
  const handleClose = () => setOpen(false);
  
  // Handle adding a new tag
  const handleAddTag = () => {
    if (newTag.trim() && !tags.includes(newTag.trim())) {
      setTags([...tags, newTag.trim()]);
      setNewTag('');
    }
  };
  
  // Handle removing a tag
  const handleDeleteTag = (tagToDelete) => {
    setTags(tags.filter(tag => tag !== tagToDelete));
  };
  
  // Handle key press in tag input
  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      handleAddTag();
    }
  };
  
  // Handle save
  const handleSave = () => {
    onSave({
      ...video,
      tags,
      color,
      folder
    });
    handleClose();
  };
  
  return (
    <>
      <Button
        variant="outlined"
        startIcon={<LabelIcon />}
        onClick={handleOpen}
        size={isMobile ? "small" : "medium"}
        sx={{ mt: 2 }}
      >
        Edit Tags & Organization
      </Button>
      
      <Dialog 
        open={open} 
        onClose={handleClose}
        fullWidth
        maxWidth="sm"
      >
        <DialogTitle>
          Edit Tags & Organization
        </DialogTitle>
        
        <DialogContent dividers>
          {/* Tags Section */}
          <Box sx={{ mb: 3 }}>
            <Typography variant="subtitle1" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
              <LabelIcon sx={{ mr: 1 }} /> Tags
            </Typography>
            
            <Box sx={{ display: 'flex', mb: 1 }}>
              <TextField
                fullWidth
                size="small"
                label="Add tag"
                value={newTag}
                onChange={(e) => setNewTag(e.target.value)}
                onKeyPress={handleKeyPress}
                sx={{ mr: 1 }}
              />
              <Button 
                variant="contained" 
                onClick={handleAddTag}
                disabled={!newTag.trim()}
              >
                <AddIcon />
              </Button>
            </Box>
            
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
              {tags.map(tag => (
                <Chip
                  key={tag}
                  label={tag}
                  onDelete={() => handleDeleteTag(tag)}
                  color="primary"
                  variant="outlined"
                />
              ))}
              {tags.length === 0 && (
                <Typography variant="body2" color="text.secondary">
                  No tags added yet
                </Typography>
              )}
            </Box>
          </Box>
          
          {/* Color Section */}
          <Box sx={{ mb: 3 }}>
            <Typography variant="subtitle1" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
              <ColorIcon sx={{ mr: 1 }} /> Color Label
            </Typography>
            
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
              {colorOptions.map(colorOption => (
                <Tooltip title={colorOption.name} key={colorOption.value}>
                  <Box
                    onClick={() => setColor(colorOption.value)}
                    sx={{
                      width: 32,
                      height: 32,
                      bgcolor: colorOption.value,
                      borderRadius: '50%',
                      cursor: 'pointer',
                      border: color === colorOption.value ? '2px solid black' : '2px solid transparent',
                      '&:hover': {
                        opacity: 0.8,
                        transform: 'scale(1.1)'
                      },
                      transition: 'all 0.2s'
                    }}
                  />
                </Tooltip>
              ))}
              
              {color && (
                <Tooltip title="Clear color">
                  <IconButton onClick={() => setColor('')} size="small">
                    <CloseIcon />
                  </IconButton>
                </Tooltip>
              )}
            </Box>
          </Box>
          
          {/* Folder Section */}
          <Box>
            <Typography variant="subtitle1" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
              <FolderIcon sx={{ mr: 1 }} /> Folder
            </Typography>
            
            <FormControl fullWidth>
              <InputLabel id="folder-select-label">Folder</InputLabel>
              <Select
                labelId="folder-select-label"
                id="folder-select"
                value={folder}
                label="Folder"
                onChange={(e) => setFolder(e.target.value)}
              >
                {folderOptions.map(option => (
                  <MenuItem key={option} value={option}>
                    <Box sx={{ display: 'flex', alignItems: 'center' }}>
                      <FolderIcon sx={{ mr: 1, color: 'action.active' }} />
                      {option}
                    </Box>
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Box>
        </DialogContent>
        
        <DialogActions>
          <Button onClick={handleClose}>Cancel</Button>
          <Button onClick={handleSave} variant="contained">Save</Button>
        </DialogActions>
      </Dialog>
    </>
  );
};

export default VideoTagsEditor;
