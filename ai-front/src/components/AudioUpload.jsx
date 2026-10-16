import { useRef, useState } from 'react';

// 语音模态的底部上传控件:选择本地音频文件,回调 onUpload(file)。
export default function AudioUpload({ onUpload, disabled }) {
  const inputRef = useRef(null);
  const [fileName, setFileName] = useState('');

  const handleChange = (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setFileName(file.name);
    onUpload(file);
    e.target.value = ''; // 允许重复选同一文件
  };

  return (
    <div className="audio-upload">
      <input
        ref={inputRef}
        className="audio-upload__input"
        type="file"
        accept="audio/*"
        onChange={handleChange}
      />
      <button
        type="button"
        className="audio-upload__btn"
        onClick={() => inputRef.current?.click()}
        disabled={disabled}
      >
        {disabled ? '转写中…' : '上传语音文件'}
      </button>
      {fileName && (
        <span className="audio-upload__file" title={fileName}>
          {fileName}
        </span>
      )}
    </div>
  );
}
