"use client"

import type React from "react"

import { useState } from "react"
import { useMutation } from "@tanstack/react-query"
import { api } from "../services/api"
import { Phone, Mail, AlertTriangle, Droplets, FileText, MessageSquare, CheckCircle } from "lucide-react"

export function PublicServicesPage() {
  const [activeService, setActiveService] = useState<"leak" | "complaint" | "request" | "info">("leak")
  const [submittedRequests, setSubmittedRequests] = useState<Array<{
    id: string
    type: 'leak' | 'complaint' | 'request'
    title: string
    protocol: string
    status: 'pending' | 'in_progress' | 'resolved'
    created_at: string
  }>>([])
  const [leakReport, setLeakReport] = useState({
    location: "",
    description: "",
    citizen_name: "",
    contact: "",
  })
  const [complaint, setComplaint] = useState({
    type: "water_quality",
    description: "",
    citizen_name: "",
    contact: "",
    location: "",
  })

  const [request, setRequest] = useState({
    type: "religacao",
    description: "",
    citizen_name: "",
    contact: "",
    location: "",
    property_number: "",
  })

    // Report leak mutation
  const reportLeakMutation = useMutation({
    mutationFn: (data: any) => api.post("/monitoring/leak-reports", data),
    onSuccess: () => {
      const protocol = `VAZ-${Date.now().toString().slice(-6)}`
      setSubmittedRequests(prev => [...prev, {
        id: Date.now().toString(),
        type: 'leak',
        title: 'Reporte de Vazamento',
        protocol,
        status: 'pending',
        created_at: new Date().toISOString()
      }])
      setLeakReport({
        location: "",
        description: "",
        citizen_name: "",
        contact: "",
      })
      alert(`Vazamento reportado com sucesso! Protocolo: ${protocol}`)
    },
  })

  // Submit complaint mutation
  const submitComplaintMutation = useMutation({
    mutationFn: (data: any) => api.post("/maintenance/complaints", data),
    onSuccess: () => {
      const protocol = `REC-${Date.now().toString().slice(-6)}`
      setSubmittedRequests(prev => [...prev, {
        id: Date.now().toString(),
        type: 'complaint',
        title: 'Reclamação',
        protocol,
        status: 'pending',
        created_at: new Date().toISOString()
      }])
      setComplaint({
        type: "water_quality",
        description: "",
        citizen_name: "",
        contact: "",
        location: "",
      })
      alert(`Reclamação enviada com sucesso! Protocolo: ${protocol}`)
    },
  })

  // Submit request mutation
  const submitRequestMutation = useMutation({
    mutationFn: (data: any) => api.post("/support/requests", data),
    onSuccess: () => {
      const protocol = `SOL-${Date.now().toString().slice(-6)}`
      setSubmittedRequests(prev => [...prev, {
        id: Date.now().toString(),
        type: 'request',
        title: 'Solicitação de Serviço',
        protocol,
        status: 'pending',
        created_at: new Date().toISOString()
      }])
      setRequest({
        type: "religacao",
        description: "",
        citizen_name: "",
        contact: "",
        location: "",
        property_number: "",
      })
      alert(`Solicitação enviada com sucesso! Protocolo: ${protocol}`)
    },
  })

  const handleLeakSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    reportLeakMutation.mutate(leakReport)
  }

  const handleComplaintSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    submitComplaintMutation.mutate(complaint)
  }

  const handleRequestSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    submitRequestMutation.mutate(request)
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-slate-100">
      {/* Header */}
      <div className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center space-x-4">
            <div className="w-12 h-12 bg-blue-600 rounded-lg flex items-center justify-center">
              <Droplets className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-gray-900">SADAE - Serviços Públicos</h1>
              <p className="text-gray-600">Sistema de Análise de Dados de Abastecimento e Esgoto</p>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Service Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <button
            onClick={() => setActiveService("leak")}
            className={`p-6 rounded-lg border-2 transition-all ${
              activeService === "leak" ? "border-blue-500 bg-blue-50" : "border-gray-200 bg-white hover:border-gray-300"
            }`}
          >
            <AlertTriangle className="w-8 h-8 text-red-500 mb-4" />
            <h3 className="text-lg font-semibold text-gray-900 mb-2">Reportar Vazamento</h3>
            <p className="text-gray-600 text-sm">
              Informe vazamentos de água na sua região para que nossa equipe possa tomar as providências necessárias.
            </p>
          </button>

          <button
            onClick={() => setActiveService("complaint")}
            className={`p-6 rounded-lg border-2 transition-all ${
              activeService === "complaint"
                ? "border-blue-500 bg-blue-50"
                : "border-gray-200 bg-white hover:border-gray-300"
            }`}
          >
            <FileText className="w-8 h-8 text-blue-500 mb-4" />
            <h3 className="text-lg font-semibold text-gray-900 mb-2">Fazer Reclamação</h3>
            <p className="text-gray-600 text-sm">
              Registre reclamações sobre qualidade da água, falta de abastecimento ou outros problemas.
            </p>
          </button>

          <button
            onClick={() => setActiveService("request")}
            className={`p-6 rounded-lg border-2 transition-all ${
              activeService === "request" ? "border-blue-500 bg-blue-50" : "border-gray-200 bg-white hover:border-gray-300"
            }`}
          >
            <MessageSquare className="w-8 h-8 text-green-500 mb-4" />
            <h3 className="text-lg font-semibold text-gray-900 mb-2">Solicitar Serviço</h3>
            <p className="text-gray-600 text-sm">
              Solicite religação, instalação de medidor, mudança de titularidade e outros serviços.
            </p>
          </button>

          <button
            onClick={() => setActiveService("info")}
            className={`p-6 rounded-lg border-2 transition-all ${
              activeService === "info" ? "border-blue-500 bg-blue-50" : "border-gray-200 bg-white hover:border-gray-300"
            }`}
          >
            <Phone className="w-8 h-8 text-green-500 mb-4" />
            <h3 className="text-lg font-semibold text-gray-900 mb-2">Informações</h3>
            <p className="text-gray-600 text-sm">
              Consulte informações sobre qualidade da água, interrupções programadas e contatos úteis.
            </p>
          </button>
        </div>

        {/* Content */}
        <div className="bg-white rounded-lg shadow-lg p-8">
          {activeService === "leak" && (
            <div>
              <h2 className="text-2xl font-bold text-gray-900 mb-6">Reportar Vazamento</h2>
              <form onSubmit={handleLeakSubmit} className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Seu Nome</label>
                    <input
                      type="text"
                      required
                      value={leakReport.citizen_name}
                      onChange={(e) => setLeakReport((prev) => ({ ...prev, citizen_name: e.target.value }))}
                      className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      placeholder="Digite seu nome completo"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Contato (Telefone ou Email)</label>
                    <input
                      type="text"
                      required
                      value={leakReport.contact}
                      onChange={(e) => setLeakReport((prev) => ({ ...prev, contact: e.target.value }))}
                      className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      placeholder="(11) 99999-9999 ou email@exemplo.com"
                    />
                  </div>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Localização do Vazamento</label>
                  <input
                    type="text"
                    required
                    value={leakReport.location}
                    onChange={(e) => setLeakReport((prev) => ({ ...prev, location: e.target.value }))}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    placeholder="Endereço completo ou ponto de referência"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Descrição do Vazamento</label>
                  <textarea
                    required
                    rows={4}
                    value={leakReport.description}
                    onChange={(e) => setLeakReport((prev) => ({ ...prev, description: e.target.value }))}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    placeholder="Descreva o vazamento: intensidade, localização exata, há quanto tempo foi observado, etc."
                  />
                </div>
                <button
                  type="submit"
                  disabled={reportLeakMutation.isPending}
                  className="w-full bg-red-600 text-white py-3 px-6 rounded-lg font-medium hover:bg-red-700 focus:ring-2 focus:ring-red-500 focus:ring-offset-2 disabled:opacity-50"
                >
                  {reportLeakMutation.isPending ? "Enviando..." : "Reportar Vazamento"}
                </button>
              </form>
            </div>
          )}

          {activeService === "complaint" && (
            <div>
              <h2 className="text-2xl font-bold text-gray-900 mb-6">Fazer Reclamação</h2>
              <form onSubmit={handleComplaintSubmit} className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Seu Nome</label>
                    <input
                      type="text"
                      required
                      value={complaint.citizen_name}
                      onChange={(e) => setComplaint((prev) => ({ ...prev, citizen_name: e.target.value }))}
                      className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      placeholder="Digite seu nome completo"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Contato</label>
                    <input
                      type="text"
                      required
                      value={complaint.contact}
                      onChange={(e) => setComplaint((prev) => ({ ...prev, contact: e.target.value }))}
                      className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      placeholder="Telefone ou email para contato"
                    />
                  </div>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Tipo de Reclamação</label>
                    <select
                      value={complaint.type}
                      onChange={(e) => setComplaint((prev) => ({ ...prev, type: e.target.value }))}
                      className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    >
                      <option value="water_quality">Qualidade da Água</option>
                      <option value="no_water">Falta de Água</option>
                      <option value="low_pressure">Pressão Baixa</option>
                      <option value="billing">Problema na Fatura</option>
                      <option value="service">Atendimento</option>
                      <option value="other">Outros</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Localização</label>
                    <input
                      type="text"
                      required
                      value={complaint.location}
                      onChange={(e) => setComplaint((prev) => ({ ...prev, location: e.target.value }))}
                      className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      placeholder="Endereço onde ocorre o problema"
                    />
                  </div>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Descrição da Reclamação</label>
                  <textarea
                    required
                    rows={4}
                    value={complaint.description}
                    onChange={(e) => setComplaint((prev) => ({ ...prev, description: e.target.value }))}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    placeholder="Descreva detalhadamente o problema que você está enfrentando..."
                  />
                </div>
                <button
                  type="submit"
                  disabled={submitComplaintMutation.isPending}
                  className="w-full bg-blue-600 text-white py-3 px-6 rounded-lg font-medium hover:bg-blue-700 focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50"
                >
                  {submitComplaintMutation.isPending ? "Enviando..." : "Enviar Reclamação"}
                </button>
              </form>
            </div>
          )}

          {activeService === "request" && (
            <div>
              <h2 className="text-2xl font-bold text-gray-900 mb-6">Solicitar Serviço</h2>
              <form onSubmit={handleRequestSubmit} className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Seu Nome</label>
                    <input
                      type="text"
                      required
                      value={request.citizen_name}
                      onChange={(e) => setRequest((prev) => ({ ...prev, citizen_name: e.target.value }))}
                      className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      placeholder="Digite seu nome completo"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Contato</label>
                    <input
                      type="text"
                      required
                      value={request.contact}
                      onChange={(e) => setRequest((prev) => ({ ...prev, contact: e.target.value }))}
                      className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      placeholder="Telefone ou email para contato"
                    />
                  </div>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Tipo de Solicitação</label>
                    <select
                      value={request.type}
                      onChange={(e) => setRequest((prev) => ({ ...prev, type: e.target.value }))}
                      className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    >
                      <option value="religacao">Religação de Água</option>
                      <option value="medidor">Instalação de Medidor</option>
                      <option value="titularidade">Mudança de Titularidade</option>
                      <option value="ramal">Ligação de Ramal</option>
                      <option value="outros">Outros</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Número do Imóvel</label>
                    <input
                      type="text"
                      required
                      value={request.property_number}
                      onChange={(e) => setRequest((prev) => ({ ...prev, property_number: e.target.value }))}
                      className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      placeholder="Número do imóvel ou cliente"
                    />
                  </div>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Localização</label>
                  <input
                    type="text"
                    required
                    value={request.location}
                    onChange={(e) => setRequest((prev) => ({ ...prev, location: e.target.value }))}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    placeholder="Endereço completo"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Descrição da Solicitação</label>
                  <textarea
                    required
                    rows={4}
                    value={request.description}
                    onChange={(e) => setRequest((prev) => ({ ...prev, description: e.target.value }))}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    placeholder="Descreva detalhadamente o serviço que você precisa..."
                  />
                </div>
                <button
                  type="submit"
                  disabled={submitRequestMutation.isPending}
                  className="w-full bg-green-600 text-white py-3 px-6 rounded-lg font-medium hover:bg-green-700 focus:ring-2 focus:ring-green-500 focus:ring-offset-2 disabled:opacity-50"
                >
                  {submitRequestMutation.isPending ? "Enviando..." : "Enviar Solicitação"}
                </button>
              </form>
            </div>
          )}

          {activeService === "info" && (
            <div>
              <h2 className="text-2xl font-bold text-gray-900 mb-6">Informações e Contatos</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">Qualidade da Água</h3>
                  <div className="space-y-3">
                    <div className="flex items-center space-x-3">
                      <div className="w-3 h-3 bg-green-500 rounded-full"></div>
                      <span className="text-sm text-gray-700">Qualidade: Excelente (98%)</span>
                    </div>
                    <div className="flex items-center space-x-3">
                      <div className="w-3 h-3 bg-blue-500 rounded-full"></div>
                      <span className="text-sm text-gray-700">pH: 7.2 (Ideal)</span>
                    </div>
                    <div className="flex items-center space-x-3">
                      <div className="w-3 h-3 bg-green-500 rounded-full"></div>
                      <span className="text-sm text-gray-700">Cloro: 0.8 mg/L (Adequado)</span>
                    </div>
                  </div>
                </div>

                <div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">Status do Sistema</h3>
                  <div className="space-y-3">
                    <div className="flex items-center space-x-3">
                      <div className="w-3 h-3 bg-green-500 rounded-full"></div>
                      <span className="text-sm text-gray-700">Abastecimento: Normal</span>
                    </div>
                    <div className="flex items-center space-x-3">
                      <div className="w-3 h-3 bg-green-500 rounded-full"></div>
                      <span className="text-sm text-gray-700">Pressão: 3.2 bar (Adequada)</span>
                    </div>
                    <div className="flex items-center space-x-3">
                      <div className="w-3 h-3 bg-yellow-500 rounded-full"></div>
                      <span className="text-sm text-gray-700">Manutenção programada: Zona Sul (15/12)</span>
                    </div>
                  </div>
                </div>

                <div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">Contatos de Emergência</h3>
                  <div className="space-y-3">
                    <div className="flex items-center space-x-3">
                      <Phone className="w-4 h-4 text-red-500" />
                      <span className="text-sm text-gray-700">Emergência 24h: 0800-123-4567</span>
                    </div>
                    <div className="flex items-center space-x-3">
                      <Phone className="w-4 h-4 text-blue-500" />
                      <span className="text-sm text-gray-700">Atendimento: (11) 3456-7890</span>
                    </div>
                    <div className="flex items-center space-x-3">
                      <Mail className="w-4 h-4 text-green-500" />
                      <span className="text-sm text-gray-700">Email: atendimento@sadae.gov.br</span>
                    </div>
                  </div>
                </div>

                <div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">Horários de Atendimento</h3>
                  <div className="space-y-2 text-sm text-gray-700">
                    <p>
                      <strong>Segunda a Sexta:</strong> 8h às 18h
                    </p>
                    <p>
                      <strong>Sábado:</strong> 8h às 12h
                    </p>
                    <p>
                      <strong>Domingo:</strong> Apenas emergências
                    </p>
                    <p>
                      <strong>Emergências:</strong> 24h por dia
                    </p>
                  </div>
                </div>
              </div>

              <div className="mt-8 p-4 bg-blue-50 rounded-lg">
                <h4 className="font-semibold text-blue-900 mb-2">💡 Dica Importante</h4>
                <p className="text-blue-800 text-sm">
                  Para um atendimento mais rápido, tenha em mãos seu número de cliente ou endereço completo ao entrar em
                  contato conosco.
                </p>
              </div>
            </div>
          )}
        </div>

        {/* Submitted Requests Tracking */}
        {submittedRequests.length > 0 && (
          <div className="mt-8 bg-white rounded-lg shadow-lg p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
              <CheckCircle className="w-5 h-5 text-green-500 mr-2" />
              Acompanhe suas Solicitações
            </h3>
            <div className="space-y-3">
              {submittedRequests.map((req) => (
                <div key={req.id} className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                  <div className="flex-1">
                    <div className="flex items-center space-x-3">
                      <span className="font-mono text-sm text-gray-600">#{req.protocol}</span>
                      <span className="text-sm font-medium text-gray-900">{req.title}</span>
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                        req.status === 'pending' ? 'bg-yellow-100 text-yellow-800' :
                        req.status === 'in_progress' ? 'bg-blue-100 text-blue-800' :
                        'bg-green-100 text-green-800'
                      }`}>
                        {req.status === 'pending' ? 'Pendente' :
                         req.status === 'in_progress' ? 'Em Andamento' : 'Resolvido'}
                      </span>
                    </div>
                    <p className="text-xs text-gray-500 mt-1">
                      Criado em: {new Date(req.created_at).toLocaleString('pt-BR')}
                    </p>
                  </div>
                  <button className="text-blue-600 hover:text-blue-800 text-sm font-medium">
                    Ver Detalhes
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Footer */}
        <div className="mt-8 text-center text-gray-600">
          <p className="text-sm">© 2024 SADAE - Sistema de Análise de Dados de Abastecimento e Esgoto</p>
          <p className="text-xs mt-1">Desenvolvido para melhor atender a população com transparência e eficiência</p>
        </div>
      </div>
    </div>
  )
}
