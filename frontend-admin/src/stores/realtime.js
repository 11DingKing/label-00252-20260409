import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useRealtimeStore = defineStore('realtime', () => {
  const connected = ref(false)
  const state = ref({})
  const history = ref([])
  const maxHistory = 60
  const activeAlarmCount = ref(0)

  const summary = computed(() => state.value.summary || {})
  const pvData = computed(() => state.value.pv || {})
  const windData = computed(() => state.value.wind || {})
  const batteryData = computed(() => state.value.battery || {})
  const loadData = computed(() => state.value.load || {})
  const gridData = computed(() => state.value.grid || {})

  function updateState(newState) {
    state.value = newState
    history.value.push({
      timestamp: new Date(),
      ...newState.summary
    })
    if (history.value.length > maxHistory) {
      history.value.shift()
    }
  }

  function setConnected(value) {
    connected.value = value
  }

  function clearHistory() {
    history.value = []
  }

  function setActiveAlarmCount(count) {
    activeAlarmCount.value = count
  }

  return {
    connected,
    state,
    history,
    summary,
    pvData,
    windData,
    batteryData,
    loadData,
    gridData,
    activeAlarmCount,
    updateState,
    setConnected,
    clearHistory,
    setActiveAlarmCount
  }
})
