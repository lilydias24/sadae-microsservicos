export const mockMonitoringData = [
  {
    id: "EVT-001",
    status: "Crítico",
    component: "API Gateway",
    message: "Latência acima de 2000ms",
    timestamp: new Date(Date.now() - 2 * 60 * 1000).toISOString(), // 2 min atrás
  },
  {
    id: "EVT-002",
    status: "Atenção",
    component: "Serviço de Autenticação",
    message: "Taxa de erro de login em 5%",
    timestamp: new Date(Date.now() - 10 * 60 * 1000).toISOString(), // 10 min atrás
  },
  {
    id: "EVT-003",
    status: "Resolvido",
    component: "Banco de Dados",
    message: "Uso de CPU normalizado",
    timestamp: new Date(Date.now() - 30 * 60 * 1000).toISOString(), // 30 min atrás
  },
  {
    id: "EVT-004",
    status: "Info",
    component: "Worker de E-mails",
    message: "150 e-mails enviados na última hora",
    timestamp: new Date(Date.now() - 60 * 60 * 1000).toISOString(), // 1 hora atrás
  },
  {
    id: "EVT-005",
    status: "Crítico",
    component: "Servidor Web-01",
    message: "Servidor não responde (timeout)",
    timestamp: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(), // 2 horas atrás
  },
];