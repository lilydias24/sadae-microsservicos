import jsPDF from 'jspdf';

// Interface para dados da fatura
interface Bill {
    id: string;
    customer_id: string;
    amount: number;
    consumption: number;
    due_date: string;
    status: string;
    created_at: string;
    period_start: string;
    period_end: string;
}

/**
 * Gera um PDF da fatura com os dados fornecidos
 * @param bill Dados da fatura
 */
export const generateBillPDF = (bill: Bill): void => {
    const doc = new jsPDF();

    // Configurações
    const pageWidth = doc.internal.pageSize.getWidth();
    const margin = 20;
    let yPosition = 20;

    // Função auxiliar para formatar moeda
    const formatCurrency = (value: number): string => {
        return new Intl.NumberFormat('pt-BR', {
            style: 'currency',
            currency: 'BRL'
        }).format(value);
    };

    // Função auxiliar para formatar data
    const formatDate = (dateString: string): string => {
        const date = new Date(dateString);
        return date.toLocaleDateString('pt-BR');
    };

    // Cabeçalho
    doc.setFillColor(41, 128, 185);
    doc.rect(0, 0, pageWidth, 40, 'F');

    doc.setTextColor(255, 255, 255);
    doc.setFontSize(24);
    doc.text('SADAE', margin, 25);

    doc.setFontSize(12);
    doc.text('Sistema de Abastecimento de Água e Esgoto', margin, 33);

    yPosition = 55;

    // Título da Fatura
    doc.setTextColor(0, 0, 0);
    doc.setFontSize(18);
    doc.text('FATURA DE ÁGUA', margin, yPosition);

    yPosition += 15;

    // Informações da Fatura
    doc.setFontSize(11);
    doc.setFont('helvetica', 'bold');
    doc.text(`Número da Fatura: #${bill.id.slice(-8)}`, margin, yPosition);

    yPosition += 7;
    doc.setFont('helvetica', 'normal');
    doc.text(`Data de Emissão: ${formatDate(bill.created_at)}`, margin, yPosition);

    yPosition += 7;
    doc.text(`Cliente ID: ${bill.customer_id}`, margin, yPosition);

    yPosition += 15;

    // Linha separadora
    doc.setDrawColor(200, 200, 200);
    doc.line(margin, yPosition, pageWidth - margin, yPosition);

    yPosition += 15;

    // Período de Consumo
    doc.setFont('helvetica', 'bold');
    doc.setFontSize(14);
    doc.text('Período de Consumo', margin, yPosition);

    yPosition += 10;
    doc.setFont('helvetica', 'normal');
    doc.setFontSize(11);
    doc.text(`De: ${formatDate(bill.period_start)}`, margin, yPosition);

    yPosition += 7;
    doc.text(`Até: ${formatDate(bill.period_end)}`, margin, yPosition);

    yPosition += 15;

    // Linha separadora
    doc.line(margin, yPosition, pageWidth - margin, yPosition);

    yPosition += 15;

    // Consumo de Água
    doc.setFont('helvetica', 'bold');
    doc.setFontSize(14);
    doc.text('Consumo de Água', margin, yPosition);

    yPosition += 10;

    // Box de consumo
    doc.setFillColor(240, 248, 255);
    doc.roundedRect(margin, yPosition, pageWidth - 2 * margin, 20, 3, 3, 'F');

    doc.setFont('helvetica', 'normal');
    doc.setFontSize(11);
    doc.text(`Volume consumido:`, margin + 5, yPosition + 8);

    doc.setFont('helvetica', 'bold');
    doc.setFontSize(16);
    doc.setTextColor(41, 128, 185);
    doc.text(`${bill.consumption} m³`, margin + 5, yPosition + 16);

    yPosition += 30;

    // Detalhamento da Fatura
    doc.setTextColor(0, 0, 0);
    doc.setFont('helvetica', 'bold');
    doc.setFontSize(14);
    doc.text('Detalhamento da Fatura', margin, yPosition);

    yPosition += 10;

    // Tabela de valores
    doc.setFont('helvetica', 'normal');
    doc.setFontSize(11);

    const waterCharge = bill.amount * 0.75;
    const sewerCharge = bill.amount * 0.20;
    const municipalTaxes = bill.amount * 0.05;

    // Linha 1 - Consumo de água
    doc.text(`Consumo de Água (${bill.consumption} m³)`, margin, yPosition);
    doc.text(formatCurrency(waterCharge), pageWidth - margin - 30, yPosition, { align: 'right' });

    yPosition += 7;

    // Linha 2 - Taxa de esgoto
    doc.text('Taxa de Esgoto', margin, yPosition);
    doc.text(formatCurrency(sewerCharge), pageWidth - margin - 30, yPosition, { align: 'right' });

    yPosition += 7;

    // Linha 3 - Taxas municipais
    doc.text('Taxas Municipais', margin, yPosition);
    doc.text(formatCurrency(municipalTaxes), pageWidth - margin - 30, yPosition, { align: 'right' });

    yPosition += 12;

    // Linha separadora
    doc.setLineWidth(0.5);
    doc.line(margin, yPosition, pageWidth - margin, yPosition);

    yPosition += 10;

    // Total
    doc.setFont('helvetica', 'bold');
    doc.setFontSize(14);
    doc.text('Total a Pagar:', margin, yPosition);

    doc.setFontSize(18);
    doc.setTextColor(220, 53, 69);
    doc.text(formatCurrency(bill.amount), pageWidth - margin - 30, yPosition, { align: 'right' });

    yPosition += 13;

    // Data de Vencimento
    doc.setTextColor(0, 0, 0);
    doc.setFontSize(12);
    doc.setFont('helvetica', 'bold');
    doc.text('Vencimento:', margin, yPosition);

    doc.setTextColor(220, 53, 69);
    doc.text(formatDate(bill.due_date), margin + 35, yPosition);

    yPosition += 20;

    // Linha separadora
    doc.setTextColor(0, 0, 0);
    doc.setLineWidth(0.3);
    doc.line(margin, yPosition, pageWidth - margin, yPosition);

    yPosition += 10;

    // Status da Fatura
    doc.setFont('helvetica', 'bold');
    doc.setFontSize(11);
    doc.text('Status:', margin, yPosition);

    doc.setFont('helvetica', 'normal');
    let statusText = '';
    let statusColor: [number, number, number] = [0, 0, 0];

    switch (bill.status) {
        case 'paid':
            statusText = 'Paga';
            statusColor = [40, 167, 69];
            break;
        case 'pending':
            statusText = 'Pendente';
            statusColor = [255, 193, 7];
            break;
        case 'overdue':
            statusText = 'Vencida';
            statusColor = [220, 53, 69];
            break;
        default:
            statusText = bill.status;
    }

    doc.setTextColor(...statusColor);
    doc.text(statusText, margin + 20, yPosition);

    // Função para desenhar código de barras (demonstração)
    const drawBarcode = (x: number, y: number, width: number, height: number) => {
        // Padrão fixo de barras para demonstração (simula um código de barras Code 128)
        // 1 = barra preta, 0 = espaço branco
        const pattern = '11011010001101101110111010111011101110101110001011101000101110101000111010100010001011101110101110111011101010001010001';

        const barWidth = width / pattern.length;

        doc.setFillColor(0, 0, 0); // Preto para as barras

        let currentX = x;
        for (let i = 0; i < pattern.length; i++) {
            if (pattern[i] === '1') {
                doc.rect(currentX, y, barWidth, height, 'F');
            }
            currentX += barWidth;
        }

        // Número do código de barras abaixo das barras
        doc.setTextColor(0, 0, 0);
        doc.setFontSize(8);
        doc.setFont('courier', 'normal');
        const barcodeNumber = `34191.79001 01043.510047 91020.150008 1 ${new Date().getFullYear()}0000${bill.id.slice(-8)}`;
        doc.text(barcodeNumber, x + width / 2, y + height + 4, { align: 'center' });
    };

    // Rodapé - Código de Barras
    const footerY = doc.internal.pageSize.getHeight() - 25;

    // Desenhar código de barras
    const barcodeWidth = 140;
    const barcodeHeight = 12;
    const barcodeX = (pageWidth - barcodeWidth) / 2;
    const barcodeY = footerY - 10;

    drawBarcode(barcodeX, barcodeY, barcodeWidth, barcodeHeight);

    // Salvar PDF
    const fileName = `fatura_${bill.id.slice(-8)}_${new Date().getTime()}.pdf`;
    doc.save(fileName);
};
