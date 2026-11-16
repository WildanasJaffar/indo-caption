/**
 * Format seconds into mm:ss.mmm format (e.g., 01:23.450)
 */
export function formatTime(seconds) {
  if (seconds === undefined || seconds === null || isNaN(seconds)) return "00:00.000";
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60);
  const ms = Math.floor((seconds - Math.floor(seconds)) * 1000);
  return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}.${String(ms).padStart(3, '0')}`;
}

/**
 * Format seconds into hh:mm:ss for video display
 */
export function formatTimeHHMMSS(seconds) {
  if (seconds === undefined || seconds === null || isNaN(seconds)) return "00:00";
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = Math.floor(seconds % 60);
  if (h > 0) {
    return `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
  }
  return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
}

/**
 * Parses mm:ss.mmm or ss.mmm string into float seconds
 */
export function parseTime(str) {
  if (!str) return 0.0;
  const parts = str.trim().split(':');
  if (parts.length === 2) {
    const minutes = parseFloat(parts[0]) || 0;
    const seconds = parseFloat(parts[1]) || 0;
    return Math.max(0, minutes * 60 + seconds);
  }
  if (parts.length === 3) {
    const hours = parseFloat(parts[0]) || 0;
    const minutes = parseFloat(parts[1]) || 0;
    const seconds = parseFloat(parts[2]) || 0;
    return Math.max(0, hours * 3600 + minutes * 60 + seconds);
  }
  return Math.max(0, parseFloat(str) || 0);
}

