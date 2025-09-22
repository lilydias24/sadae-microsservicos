import Link from "next/link"
import { Droplets, Activity, Shield, Users, BarChart3, AlertTriangle } from "lucide-react"

export default function Page() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-slate-100">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <div className="w-12 h-12 bg-blue-600 rounded-xl flex items-center justify-center">
                <Droplets className="w-7 h-7 text-white" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-gray-900">SADAE</h1>
                <p className="text-gray-600">Sistema de Análise de Dados de Abastecimento e Esgoto</p>
              </div>
            </div>
            <div className="flex items-center space-x-4">
              <Link
                href="/frontend"
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
              >
                Acessar Sistema
              </Link>
            </div>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="text-center mb-16">
          <h2 className="text-4xl font-bold text-gray-900 mb-4">Monitoramento Inteligente de Recursos Hídricos</h2>
          <p className="text-xl text-gray-600 max-w-3xl mx-auto">
            Sistema completo para análise, monitoramento e gestão de dados de abastecimento de água e esgoto, com
            detecção automática de anomalias e gestão de crises.
          </p>
        </div>

        {/* Features Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8 mb-16">
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center mb-4">
              <Activity className="w-6 h-6 text-blue-600" />
            </div>
            <h3 className="text-lg font-semibold text-gray-900 mb-2">Monitoramento em Tempo Real</h3>
            <p className="text-gray-600">
              Acompanhe dados de sensores de pressão, fluxo, qualidade da água e precipitação em tempo real.
            </p>
          </div>

          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center mb-4">
              <Shield className="w-6 h-6 text-green-600" />
            </div>
            <h3 className="text-lg font-semibold text-gray-900 mb-2">Detecção de Anomalias</h3>
            <p className="text-gray-600">
              Sistema inteligente de detecção automática de vazamentos e anomalias na rede de distribuição.
            </p>
          </div>

          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center mb-4">
              <Users className="w-6 h-6 text-purple-600" />
            </div>
            <h3 className="text-lg font-semibold text-gray-900 mb-2">Gestão de Manutenção</h3>
            <p className="text-gray-600">
              Gerencie ordens de serviço, equipes de manutenção e reclamações dos cidadãos de forma integrada.
            </p>
          </div>

          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <div className="w-12 h-12 bg-yellow-100 rounded-lg flex items-center justify-center mb-4">
              <BarChart3 className="w-6 h-6 text-yellow-600" />
            </div>
            <h3 className="text-lg font-semibold text-gray-900 mb-2">Sistema de Faturamento</h3>
            <p className="text-gray-600">
              Coleta automática de leituras, geração de faturas e gestão de contestações e negociações.
            </p>
          </div>

          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <div className="w-12 h-12 bg-red-100 rounded-lg flex items-center justify-center mb-4">
              <AlertTriangle className="w-6 h-6 text-red-600" />
            </div>
            <h3 className="text-lg font-semibold text-gray-900 mb-2">Gestão de Crises</h3>
            <p className="text-gray-600">
              Simulação de cenários críticos, alertas à Defesa Civil e planos de mitigação de riscos.
            </p>
          </div>

          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <div className="w-12 h-12 bg-indigo-100 rounded-lg flex items-center justify-center mb-4">
              <BarChart3 className="w-6 h-6 text-indigo-600" />
            </div>
            <h3 className="text-lg font-semibold text-gray-900 mb-2">Relatórios e Analytics</h3>
            <p className="text-gray-600">
              Relatórios detalhados e análises estatísticas para tomada de decisões estratégicas.
            </p>
          </div>
        </div>

        {/* Architecture Overview */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-8 mb-16">
          <h3 className="text-2xl font-bold text-gray-900 mb-6 text-center">Arquitetura de Microsserviços</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <div className="text-center">
              <div className="w-16 h-16 bg-blue-600 rounded-lg flex items-center justify-center mx-auto mb-3">
                <Activity className="w-8 h-8 text-white" />
              </div>
              <h4 className="font-semibold text-gray-900 mb-2">Monitoramento</h4>
              <p className="text-sm text-gray-600">Sensores e detecção de anomalias</p>
            </div>
            <div className="text-center">
              <div className="w-16 h-16 bg-green-600 rounded-lg flex items-center justify-center mx-auto mb-3">
                <Users className="w-8 h-8 text-white" />
              </div>
              <h4 className="font-semibold text-gray-900 mb-2">Manutenção</h4>
              <p className="text-sm text-gray-600">Ordens de serviço e equipes</p>
            </div>
            <div className="text-center">
              <div className="w-16 h-16 bg-yellow-600 rounded-lg flex items-center justify-center mx-auto mb-3">
                <BarChart3 className="w-8 h-8 text-white" />
              </div>
              <h4 className="font-semibold text-gray-900 mb-2">Faturamento</h4>
              <p className="text-sm text-gray-600">Cobrança e contestações</p>
            </div>
            <div className="text-center">
              <div className="w-16 h-16 bg-red-600 rounded-lg flex items-center justify-center mx-auto mb-3">
                <AlertTriangle className="w-8 h-8 text-white" />
              </div>
              <h4 className="font-semibold text-gray-900 mb-2">Crises</h4>
              <p className="text-sm text-gray-600">Simulações e alertas</p>
            </div>
          </div>
        </div>

        {/* CTA Section */}
        <div className="text-center">
          <h3 className="text-2xl font-bold text-gray-900 mb-4">Pronto para começar?</h3>
          <p className="text-gray-600 mb-8 max-w-2xl mx-auto">
            Acesse o sistema completo e explore todas as funcionalidades de monitoramento e gestão de recursos hídricos.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link
              href="/frontend"
              className="px-8 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium"
            >
              Acessar Sistema Completo
            </Link>
            <Link
              href="/frontend/public"
              className="px-8 py-3 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors font-medium"
            >
              Serviços Públicos
            </Link>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="bg-white border-t mt-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="text-center text-gray-600">
            <p className="mb-2">© 2024 SADAE - Sistema de Análise de Dados de Abastecimento e Esgoto</p>
            <p className="text-sm">
              Desenvolvido com arquitetura de microsserviços para máxima escalabilidade e confiabilidade
            </p>
          </div>
        </div>
      </footer>
    </div>
  )
}
