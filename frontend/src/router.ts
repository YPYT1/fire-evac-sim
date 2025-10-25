/**
 * Vue Router 配置：为后续多页面扩展留出结构。
 */
import { createRouter, createWebHistory } from 'vue-router';

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      name: 'simulation',
      component: () => import('./views/SimulationView.vue'),
    },
  ],
});

export default router;
