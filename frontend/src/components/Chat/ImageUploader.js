import React, { useState } from 'react';
import './ImageUploader.css';

function ImageUploader({ onUpload, disabled }) {
  const [description, setDescription] = useState('');
  const [preview, setPreview] = useState(null);

  const handleFileSelect = (e) => {
    const file = e.target.files[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onloadend = () => {
      const base64 = reader.result.split(',')[1];
      setPreview(reader.result);

      // Auto-upload or wait for description
      if (description.trim()) {
        onUpload(base64, description);
        resetUploader();
      }
    };
    reader.readAsDataURL(file);
  };

  const handleUpload = () => {
    if (preview) {
      const base64 = preview.split(',')[1];
      onUpload(base64, description || 'System design diagram');
      resetUploader();
    }
  };

  const resetUploader = () => {
    setPreview(null);
    setDescription('');
  };

  return (
    <div className="image-uploader">
      {!preview ? (
        <label className="upload-button">
          📸 Upload Diagram
          <input
            type="file"
            accept="image/*"
            onChange={handleFileSelect}
            disabled={disabled}
            style={{ display: 'none' }}
          />
        </label>
      ) : (
        <div className="upload-preview">
          <img src={preview} alt="Preview" className="preview-image" />
          <input
            type="text"
            placeholder="Describe your design (optional)..."
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            className="description-input"
          />
          <div className="preview-actions">
            <button onClick={resetUploader} className="cancel-button">
              Cancel
            </button>
            <button onClick={handleUpload} className="upload-confirm-button">
              Upload →
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

export default ImageUploader;
