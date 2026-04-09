import { ref, onMounted, onUnmounted, computed } from "vue";
import { useRealtimeStore } from "@/stores/realtime";

export function useWebSocket() {
  const ws = ref(null);
  const realtimeStore = useRealtimeStore();
  let reconnectTimer = null;
  const reconnectAttempts = ref(0);
  const maxReconnectAttempts = 10;
  const isReconnecting = ref(false);

  const connectionStatus = computed(() => {
    if (realtimeStore.connected) {
      return "connected";
    } else if (isReconnecting.value) {
      return "reconnecting";
    } else {
      return "disconnected";
    }
  });

  function connect() {
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const host = window.location.host;
    const wsUrl = `${protocol}//${host}/ws/realtime`;

    console.log("Connecting to WebSocket:", wsUrl);
    ws.value = new WebSocket(wsUrl);

    ws.value.onopen = () => {
      console.log("WebSocket connected");
      realtimeStore.setConnected(true);
      isReconnecting.value = false;
      reconnectAttempts.value = 0;
    };

    ws.value.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data);
        console.log("WebSocket message received:", message.type);

        if (message.type === "state_update" && message.data) {
          realtimeStore.updateState(message.data);
        } else if (message.type === "heartbeat") {
          if (ws.value && ws.value.readyState === WebSocket.OPEN) {
            ws.value.send(JSON.stringify({ type: "ping" }));
          }
        }
      } catch (e) {
        console.error("Failed to parse WebSocket message:", e);
      }
    };

    ws.value.onclose = (event) => {
      console.log("WebSocket disconnected:", event.code, event.reason);
      realtimeStore.setConnected(false);
      scheduleReconnect();
    };

    ws.value.onerror = (error) => {
      console.error("WebSocket error:", error);
    };
  }

  function scheduleReconnect() {
    if (reconnectAttempts.value < maxReconnectAttempts) {
      isReconnecting.value = true;
      const delay = Math.min(
        1000 * Math.pow(2, reconnectAttempts.value),
        30000,
      );
      console.log(
        `Scheduling reconnect in ${delay}ms (attempt ${reconnectAttempts.value + 1})`,
      );
      reconnectTimer = setTimeout(() => {
        reconnectAttempts.value++;
        connect();
      }, delay);
    } else {
      isReconnecting.value = false;
      console.log("Max reconnect attempts reached");
    }
  }

  function disconnect() {
    if (reconnectTimer) {
      clearTimeout(reconnectTimer);
    }
    isReconnecting.value = false;
  }

  onMounted(() => {
    connect();
  });

  onUnmounted(() => {
    disconnect();
  });

  return {
    ws,
    connect,
    disconnect,
    connectionStatus,
    reconnectAttempts,
    isReconnecting,
  };
}
