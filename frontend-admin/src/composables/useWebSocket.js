import { ref, onMounted, onUnmounted, comput"vue";
import { useRealtimeStore } from "@/stores/realtime";

export function useWebSocket() {
  const ws = ref(null);
  const realtimeStore = useRealtimeStore();
  let reconnectTimer = null;
  let reconnectAttempts = 0;
  const maxReconnectAttempts = 10;

  function connect() {
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const host = window.location.host;
    const wsUrl = `${protocol}//${host}/ws/realtime`;

    console.log("Connecting to WebSocket:", wsUrl);
    ws.value = new WebSocket(wsUrl);

    ws.value.onopen = () => {
      console.log("WebSocket connected");
      realtimeStore.setConnected(true);
      reconnectAttempts = 0;
    };

    ws.value.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data);
        console.log("WebSocket message received:", message.type);

        if (message.type === "state_update" && message.data) {
          realtimeStore.updateState(message.data);
        } else if (message.type === "heartbeat") {
          // Respond to heartbeat with ping to keep connection alive
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
    if (reconnectAttempts < maxReconnectAttempts) {
      const delay = Math.min(1000 * Math.pow(2, reconnectAttempts), 30000);
      console.log(
        `Scheduling reconnect in ${delay}ms (attempt ${reconnectAttempts + 1})`,
      );
      reconnectTimer = setTimeout(() => {
        reconnectAttempts++;
        connect();
      }, delay);
    }
  }

  function disconnect() {
    if (reconnectTimer) {
      clearTimeout(reconnectTimer);
    }
    if (ws.value) {
      ws.value.close();
    }
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
  };   ws.value.close()
    }
  }

  onMounted(() => {
    connect()
  })

  onUnmounted(() => {
    disconnect()
  })

  return {
    ws,
    connect,
    disconnect,
    connectionStatus,
    reconnectAttempts,
    isReconnecting
  }
}
