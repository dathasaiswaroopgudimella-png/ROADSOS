export function useHaptics() {
  const isSupported = typeof window !== 'undefined' && 'vibrate' in navigator;

  const vibrate = (pattern: number | number[]) => {
    if (isSupported) {
      navigator.vibrate(pattern);
    }
  };

  return {
    tap: () => vibrate(50),
    confirm: () => vibrate(200),
    alert: () => vibrate([100, 50, 100]),
    emergency: () => vibrate([200, 100, 200, 100, 200])
  };
}
