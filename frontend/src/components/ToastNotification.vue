<template>
  <Transition name="toast">
    <div v-if="visible" :class="['toast', `toast--${type}`]" role="alert">
      <div class="toast__icon">{{ icon }}</div>
      <div class="toast__content">
        <p class="toast__message">{{ message }}</p>
      </div>
      <button class="toast__close" @click="close" aria-label="关闭">×</button>
    </div>
  </Transition>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue';

export interface ToastProps {
  message: string;
  type?: 'success' | 'error' | 'warning' | 'info';
  duration?: number;
  visible?: boolean;
}

const props = withDefaults(defineProps<ToastProps>(), {
  type: 'info',
  duration: 4000,
  visible: false,
});

const emit = defineEmits<{
  close: [];
}>();

const visible = ref(props.visible);
let timeoutId: number | null = null;

const icon = computed(() => {
  switch (props.type) {
    case 'success':
      return '✓';
    case 'error':
      return '✕';
    case 'warning':
      return '⚠';
    default:
      return 'ℹ';
  }
});

function close() {
  visible.value = false;
  emit('close');
}

function startTimer() {
  if (timeoutId) {
    clearTimeout(timeoutId);
  }
  if (props.duration > 0) {
    timeoutId = window.setTimeout(() => {
      close();
    }, props.duration);
  }
}

watch(
  () => props.visible,
  (newVisible) => {
    visible.value = newVisible;
    if (newVisible) {
      startTimer();
    }
  },
  { immediate: true }
);
</script>

<style scoped>
.toast {
  position: fixed;
  top: 1.5rem;
  right: 1.5rem;
  min-width: 280px;
  max-width: 420px;
  padding: 1rem 1.25rem;
  background: #ffffff;
  border-radius: 0.75rem;
  box-shadow: 0 8px 24px rgba(15, 23, 42, 0.12), 0 2px 8px rgba(15, 23, 42, 0.08);
  display: flex;
  align-items: flex-start;
  gap: 0.75rem;
  z-index: 9999;
  border-left: 4px solid currentColor;
}

.toast--success {
  color: #16a34a;
}

.toast--error {
  color: #dc2626;
}

.toast--warning {
  color: #ea580c;
}

.toast--info {
  color: #2563eb;
}

.toast__icon {
  font-size: 1.5rem;
  font-weight: bold;
  line-height: 1;
  flex-shrink: 0;
}

.toast__content {
  flex: 1;
  min-width: 0;
}

.toast__message {
  margin: 0;
  font-size: 0.95rem;
  color: #0f172a;
  word-wrap: break-word;
}

.toast__close {
  background: none;
  border: none;
  font-size: 1.5rem;
  line-height: 1;
  color: rgba(15, 23, 42, 0.4);
  cursor: pointer;
  padding: 0;
  width: 1.5rem;
  height: 1.5rem;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  transition: color 0.2s;
}

.toast__close:hover {
  color: rgba(15, 23, 42, 0.7);
}

.toast-enter-active,
.toast-leave-active {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.toast-enter-from {
  opacity: 0;
  transform: translateX(100%);
}

.toast-leave-to {
  opacity: 0;
  transform: translateY(-1rem);
}
</style>
