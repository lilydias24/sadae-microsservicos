export const mockDashboardData = {
  stats: [
    { id: 1, label: 'Total de Alertas', value: '1,234', change: '+5.4%', changeType: 'increase' },
    { id: 2, label: 'Eventos Críticos', value: '56', change: '-2.1%', changeType: 'decrease' },
    { id: 3, label: 'Sistemas Online', value: '99.8%', change: '+0.1%', changeType: 'increase' },
    { id: 4, label: 'Tempo de Resposta Médio', value: '120ms', change: '+10ms', changeType: 'increase' },
  ],
  recentActivities: [
    { id: 1, user: 'Ana Silva', action: 'Reconheceu o alerta #5821', timestamp: '2 minutos atrás' },
    { id: 2, user: 'Sistema', action: 'Novo evento crítico detectado: Falha no Servidor DB-02', timestamp: '5 minutos atrás' },
    { id: 3, user: 'Bruno Costa', action: 'Resolveu o incidente #987', timestamp: '15 minutos atrás' },
    { id: 4, user: 'Sistema', action: 'Atualização de segurança aplicada no Gateway', timestamp: '1 hora atrás' },
  ],
};