"use client";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  AlertTriangle,
  Calendar,
  DollarSign,
  Download,
  Filter,
  Search,
  TrendingDown,
  TrendingUp,
  Users,
  Activity,
  Clock,
  Target,
} from "lucide-react";
import Link from "next/link";

// Datos de ejemplo para el aging
const agingData = [
  {
    cliente: "EMPRESA ABC S.A.",
    contacto: "JUAN PEREZ",
    email: "juan@empresaabc.com",
    telefono: "+57-1-234-5678",
    total: 45250000,
    corriente: 15000000,
    dias30: 12500000,
    dias60: 10250000,
    dias90: 5000000,
    mas90: 2500000,
    facturas: 8,
    ultimoPago: "2024-01-15",
    riesgo: "MEDIO",
    tendencia: "UP",
  },
  {
    cliente: "COMERCIAL XYZ LTDA.",
    contacto: "MARIA GARCIA",
    email: "maria@comercialxyz.com",
    telefono: "+57-1-234-5679",
    total: 32800000,
    corriente: 20000000,
    dias30: 8800000,
    dias60: 4000000,
    dias90: 0,
    mas90: 0,
    facturas: 5,
    ultimoPago: "2024-01-20",
    riesgo: "BAJO",
    tendencia: "UP",
  },
  {
    cliente: "INDUSTRIAS DEF CORP.",
    contacto: "CARLOS LOPEZ",
    email: "carlos@industriasdef.com",
    telefono: "+57-1-234-5680",
    total: 67500000,
    corriente: 25000000,
    dias30: 15000000,
    dias60: 12500000,
    dias90: 10000000,
    mas90: 5000000,
    facturas: 12,
    ultimoPago: "2024-01-10",
    riesgo: "ALTO",
    tendencia: "DOWN",
  },
  {
    cliente: "SERVICIOS GHI S.A.S.",
    contacto: "ANA MARTINEZ",
    email: "ana@serviciosghi.com",
    telefono: "+57-1-234-5681",
    total: 28900000,
    corriente: 18900000,
    dias30: 10000000,
    dias60: 0,
    dias90: 0,
    mas90: 0,
    facturas: 4,
    ultimoPago: "2024-01-25",
    riesgo: "BAJO",
    tendencia: "UP",
  },
  {
    cliente: "DISTRIBUIDORA JKL",
    contacto: "ROBERTO SILVA",
    email: "roberto@distribuidorajkl.com",
    telefono: "+57-1-234-5682",
    total: 89200000,
    corriente: 30000000,
    dias30: 25000000,
    dias60: 20000000,
    dias90: 10200000,
    mas90: 4000000,
    facturas: 15,
    ultimoPago: "2024-01-08",
    riesgo: "ALTO",
    tendencia: "DOWN",
  },
];

// Calcular totales
const totales = agingData.reduce(
  (acc, item) => ({
    total: acc.total + item.total,
    corriente: acc.corriente + item.corriente,
    dias30: acc.dias30 + item.dias30,
    dias60: acc.dias60 + item.dias60,
    dias90: acc.dias90 + item.dias90,
    mas90: acc.mas90 + item.mas90,
    facturas: acc.facturas + item.facturas,
  }),
  {
    total: 0,
    corriente: 0,
    dias30: 0,
    dias60: 0,
    dias90: 0,
    mas90: 0,
    facturas: 0,
  }
);

const formatCurrency = (amount: number) => {
  return new Intl.NumberFormat("es-CO", {
    style: "currency",
    currency: "COP",
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(amount);
};

const formatCompactCurrency = (amount: number) => {
  if (amount >= 1000000000) {
    return `$${(amount / 1000000000).toFixed(1)}B`;
  }
  if (amount >= 1000000) {
    return `$${(amount / 1000000).toFixed(1)}M`;
  }
  if (amount >= 1000) {
    return `$${(amount / 1000).toFixed(0)}K`;
  }
  return `$${amount}`;
};

const getRiskColor = (riesgo: string) => {
  switch (riesgo) {
    case "ALTO":
      return "text-[#ff0066] border-[#ff0066]";
    case "MEDIO":
      return "text-[#0066ff] border-[#0066ff]";
    case "BAJO":
      return "text-[#00ff88] border-[#00ff88]";
    default:
      return "text-[#888888] border-[#333333]";
  }
};

const getTrendIcon = (tendencia: string) => {
  return tendencia === "UP" ? (
    <TrendingUp className="w-3 h-3 text-[#00ff88]" />
  ) : (
    <TrendingDown className="w-3 h-3 text-[#ff0066]" />
  );
};

export default function ExecutiveAgingDashboard() {
  const currentTime = new Date().toLocaleString("es-CO", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    hour12: false,
  });

  return (
    <div className="min-h-screen bg-[#000000] text-[#ffffff]">
      {/* Command Header */}
      <header className="border-b border-[#1a1a1a] bg-[#0a0a0a] px-8 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-8">
            <div className="flex items-center space-x-3">
              <div className="w-2 h-2 bg-[#00ff88] rounded-full animate-pulse"></div>
              <span className="text-xl font-600 tracking-tight">
                ACCOUNTS RECEIVABLE COMMAND CENTER
              </span>
            </div>
            <nav className="flex space-x-6">
              <Link
                href="#"
                className="text-[#00ff88] font-500 border-b border-[#00ff88] pb-1">
                AGING ANALYSIS
              </Link>
              <Link
                href="#"
                className="text-[#888888] hover:text-[#ffffff] transition-colors duration-300">
                COLLECTIONS
              </Link>
              <Link
                href="#"
                className="text-[#888888] hover:text-[#ffffff] transition-colors duration-300">
                FORECASTING
              </Link>
              <Link
                href="#"
                className="text-[#888888] hover:text-[#ffffff] transition-colors duration-300">
                ALERTS
              </Link>
            </nav>
          </div>
          <div className="flex items-center space-x-6">
            <div className="font-mono text-sm text-[#888888]">
              LAST UPDATE: {currentTime}
            </div>
            <Button
              className="bg-[#111111] border border-[#333333] text-[#ffffff] hover:bg-[#1a1a1a] hover:border-[#00ff88] transition-all duration-300"
              size="sm">
              <Download className="w-4 h-4 mr-2" />
              EXPORT DATA
            </Button>
          </div>
        </div>
      </header>

      <main className="p-8">
        <div className="max-w-[1600px] mx-auto space-y-8">
          {/* System Status & Controls */}
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-6">
              <div className="flex items-center space-x-2">
                <Activity className="w-5 h-5 text-[#00ff88]" />
                <span className="font-500">SYSTEM STATUS: OPERATIONAL</span>
              </div>
              <div className="flex items-center space-x-2">
                <Clock className="w-4 h-4 text-[#888888]" />
                <span className="text-[#888888] font-mono text-sm">
                  AUTO-REFRESH: 30s
                </span>
              </div>
            </div>
            <div className="flex items-center space-x-4">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-[#888888]" />
                <Input
                  placeholder="SEARCH CLIENT..."
                  className="pl-10 bg-[#111111] border-[#333333] text-[#ffffff] placeholder-[#888888] focus:border-[#00ff88] w-64"
                />
              </div>
              <Select>
                <SelectTrigger className="w-48 bg-[#111111] border-[#333333] text-[#ffffff]">
                  <SelectValue placeholder="FILTER BY RISK" />
                </SelectTrigger>
                <SelectContent className="bg-[#111111] border-[#333333]">
                  <SelectItem value="all">ALL CLIENTS</SelectItem>
                  <SelectItem value="high">HIGH RISK</SelectItem>
                  <SelectItem value="medium">MEDIUM RISK</SelectItem>
                  <SelectItem value="low">LOW RISK</SelectItem>
                </SelectContent>
              </Select>
              <Button
                variant="outline"
                size="sm"
                className="border-[#333333] text-[#888888] hover:border-[#00ff88] hover:text-[#00ff88] bg-transparent">
                <Filter className="w-4 h-4 mr-2" />
                ADVANCED
              </Button>
            </div>
          </div>

          {/* Critical Metrics Grid */}
          <div className="grid grid-cols-4 gap-6">
            <Card className="bg-[rgba(255,255,255,0.03)] border-[#1a1a1a] border-2">
              <CardContent className="p-8">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center space-x-3">
                    <DollarSign className="w-6 h-6 text-[#00ff88]" />
                    <span className="text-[#888888] font-500 text-sm tracking-wide">
                      TOTAL RECEIVABLES
                    </span>
                  </div>
                  <TrendingUp className="w-4 h-4 text-[#00ff88]" />
                </div>
                <div className="space-y-2">
                  <div className="text-3xl font-700 font-mono">
                    {formatCompactCurrency(totales.total)}
                  </div>
                  <div className="flex items-center space-x-2">
                    <span className="text-[#00ff88] text-sm font-mono">
                      +2.5%
                    </span>
                    <span className="text-[#888888] text-sm">
                      vs LAST PERIOD
                    </span>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className="bg-[rgba(255,255,255,0.03)] border-[#1a1a1a] border-2">
              <CardContent className="p-8">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center space-x-3">
                    <AlertTriangle className="w-6 h-6 text-[#ff0066]" />
                    <span className="text-[#888888] font-500 text-sm tracking-wide">
                      CRITICAL (+90D)
                    </span>
                  </div>
                  <div className="w-2 h-2 bg-[#ff0066] rounded-full animate-pulse"></div>
                </div>
                <div className="space-y-2">
                  <div className="text-3xl font-700 font-mono text-[#ff0066]">
                    {formatCompactCurrency(totales.mas90)}
                  </div>
                  <div className="flex items-center space-x-2">
                    <span className="text-[#888888] text-sm font-mono">
                      {((totales.mas90 / totales.total) * 100).toFixed(1)}%
                    </span>
                    <span className="text-[#888888] text-sm">OF TOTAL</span>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className="bg-[rgba(255,255,255,0.03)] border-[#1a1a1a] border-2">
              <CardContent className="p-8">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center space-x-3">
                    <Users className="w-6 h-6 text-[#0066ff]" />
                    <span className="text-[#888888] font-500 text-sm tracking-wide">
                      ACTIVE ACCOUNTS
                    </span>
                  </div>
                  <Target className="w-4 h-4 text-[#0066ff]" />
                </div>
                <div className="space-y-2">
                  <div className="text-3xl font-700 font-mono">
                    {agingData.length}
                  </div>
                  <div className="flex items-center space-x-2">
                    <span className="text-[#0066ff] text-sm font-mono">
                      {totales.facturas}
                    </span>
                    <span className="text-[#888888] text-sm">
                      OPEN INVOICES
                    </span>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className="bg-[rgba(255,255,255,0.03)] border-[#1a1a1a] border-2">
              <CardContent className="p-8">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center space-x-3">
                    <Calendar className="w-6 h-6 text-[#888888]" />
                    <span className="text-[#888888] font-500 text-sm tracking-wide">
                      AVG COLLECTION
                    </span>
                  </div>
                  <TrendingDown className="w-4 h-4 text-[#ff0066]" />
                </div>
                <div className="space-y-2">
                  <div className="text-3xl font-700 font-mono">
                    42<span className="text-lg text-[#888888]">D</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <span className="text-[#ff0066] text-sm font-mono">
                      +3D
                    </span>
                    <span className="text-[#888888] text-sm">vs TARGET</span>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Aging Distribution */}
          <Card className="bg-[rgba(255,255,255,0.03)] border-[#1a1a1a] border-2">
            <CardHeader className="pb-6">
              <CardTitle className="text-xl font-600 tracking-tight">
                AGING DISTRIBUTION MATRIX
              </CardTitle>
              <CardDescription className="text-[#888888]">
                Real-time breakdown by collection periods
              </CardDescription>
            </CardHeader>
            <CardContent className="p-8">
              <div className="grid grid-cols-5 gap-6">
                <div className="text-center p-6 bg-[#111111] border border-[#00ff88] border-2">
                  <div className="text-2xl font-700 font-mono text-[#00ff88] mb-2">
                    {formatCompactCurrency(totales.corriente)}
                  </div>
                  <div className="text-sm font-500 text-[#00ff88] mb-1">
                    CURRENT
                  </div>
                  <div className="text-xs font-mono text-[#888888]">
                    {((totales.corriente / totales.total) * 100).toFixed(1)}%
                  </div>
                  <div className="mt-3 h-1 bg-[#333333] rounded">
                    <div
                      className="h-full bg-[#00ff88] rounded transition-all duration-500"
                      style={{
                        width: `${(totales.corriente / totales.total) * 100}%`,
                      }}></div>
                  </div>
                </div>

                <div className="text-center p-6 bg-[#111111] border border-[#333333]">
                  <div className="text-2xl font-700 font-mono text-[#ffffff] mb-2">
                    {formatCompactCurrency(totales.dias30)}
                  </div>
                  <div className="text-sm font-500 text-[#ffffff] mb-1">
                    1-30 DAYS
                  </div>
                  <div className="text-xs font-mono text-[#888888]">
                    {((totales.dias30 / totales.total) * 100).toFixed(1)}%
                  </div>
                  <div className="mt-3 h-1 bg-[#333333] rounded">
                    <div
                      className="h-full bg-[#ffffff] rounded transition-all duration-500"
                      style={{
                        width: `${(totales.dias30 / totales.total) * 100}%`,
                      }}></div>
                  </div>
                </div>

                <div className="text-center p-6 bg-[#111111] border border-[#333333]">
                  <div className="text-2xl font-700 font-mono text-[#0066ff] mb-2">
                    {formatCompactCurrency(totales.dias60)}
                  </div>
                  <div className="text-sm font-500 text-[#0066ff] mb-1">
                    31-60 DAYS
                  </div>
                  <div className="text-xs font-mono text-[#888888]">
                    {((totales.dias60 / totales.total) * 100).toFixed(1)}%
                  </div>
                  <div className="mt-3 h-1 bg-[#333333] rounded">
                    <div
                      className="h-full bg-[#0066ff] rounded transition-all duration-500"
                      style={{
                        width: `${(totales.dias60 / totales.total) * 100}%`,
                      }}></div>
                  </div>
                </div>

                <div className="text-center p-6 bg-[#111111] border border-[#333333]">
                  <div className="text-2xl font-700 font-mono text-[#ff0066] mb-2">
                    {formatCompactCurrency(totales.dias90)}
                  </div>
                  <div className="text-sm font-500 text-[#ff0066] mb-1">
                    61-90 DAYS
                  </div>
                  <div className="text-xs font-mono text-[#888888]">
                    {((totales.dias90 / totales.total) * 100).toFixed(1)}%
                  </div>
                  <div className="mt-3 h-1 bg-[#333333] rounded">
                    <div
                      className="h-full bg-[#ff0066] rounded transition-all duration-500"
                      style={{
                        width: `${(totales.dias90 / totales.total) * 100}%`,
                      }}></div>
                  </div>
                </div>

                <div className="text-center p-6 bg-[#111111] border border-[#ff0066] border-2">
                  <div className="text-2xl font-700 font-mono text-[#ff0066] mb-2">
                    {formatCompactCurrency(totales.mas90)}
                  </div>
                  <div className="text-sm font-500 text-[#ff0066] mb-1">
                    +90 DAYS
                  </div>
                  <div className="text-xs font-mono text-[#888888]">
                    {((totales.mas90 / totales.total) * 100).toFixed(1)}%
                  </div>
                  <div className="mt-3 h-1 bg-[#333333] rounded">
                    <div
                      className="h-full bg-[#ff0066] rounded transition-all duration-500 animate-pulse"
                      style={{
                        width: `${(totales.mas90 / totales.total) * 100}%`,
                      }}></div>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Client Analysis Table */}
          <Card className="bg-[rgba(255,255,255,0.03)] border-[#1a1a1a] border-2">
            <CardHeader className="pb-6">
              <CardTitle className="text-xl font-600 tracking-tight">
                CLIENT RISK ANALYSIS
              </CardTitle>
              <CardDescription className="text-[#888888]">
                Detailed aging breakdown with risk assessment
              </CardDescription>
            </CardHeader>
            <CardContent className="p-0">
              <div className="overflow-x-auto">
                <Table>
                  <TableHeader>
                    <TableRow className="border-[#333333] hover:bg-[#111111]">
                      <TableHead className="text-[#888888] font-500 text-xs tracking-wider py-4 px-8">
                        CLIENT
                      </TableHead>
                      <TableHead className="text-[#888888] font-500 text-xs tracking-wider text-right">
                        TOTAL
                      </TableHead>
                      <TableHead className="text-[#888888] font-500 text-xs tracking-wider text-right">
                        CURRENT
                      </TableHead>
                      <TableHead className="text-[#888888] font-500 text-xs tracking-wider text-right">
                        1-30D
                      </TableHead>
                      <TableHead className="text-[#888888] font-500 text-xs tracking-wider text-right">
                        31-60D
                      </TableHead>
                      <TableHead className="text-[#888888] font-500 text-xs tracking-wider text-right">
                        61-90D
                      </TableHead>
                      <TableHead className="text-[#888888] font-500 text-xs tracking-wider text-right">
                        +90D
                      </TableHead>
                      <TableHead className="text-[#888888] font-500 text-xs tracking-wider text-center">
                        RISK
                      </TableHead>
                      <TableHead className="text-[#888888] font-500 text-xs tracking-wider text-center">
                        TREND
                      </TableHead>
                      <TableHead className="text-[#888888] font-500 text-xs tracking-wider text-center">
                        INV
                      </TableHead>
                      <TableHead className="text-[#888888] font-500 text-xs tracking-wider">
                        LAST PAYMENT
                      </TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {agingData.map((cliente, index) => (
                      <TableRow
                        key={index}
                        className="border-[#333333] hover:bg-[#111111] transition-colors duration-200">
                        <TableCell className="py-6 px-8">
                          <div className="space-y-1">
                            <div className="font-600 text-[#ffffff] tracking-tight">
                              {cliente.cliente}
                            </div>
                            <div className="text-sm text-[#888888] font-mono">
                              {cliente.contacto}
                            </div>
                            <div className="text-xs text-[#444444] font-mono">
                              {cliente.email}
                            </div>
                          </div>
                        </TableCell>
                        <TableCell className="text-right font-mono font-600 text-[#ffffff]">
                          {formatCompactCurrency(cliente.total)}
                        </TableCell>
                        <TableCell className="text-right font-mono text-[#00ff88]">
                          {formatCompactCurrency(cliente.corriente)}
                        </TableCell>
                        <TableCell className="text-right font-mono text-[#ffffff]">
                          {formatCompactCurrency(cliente.dias30)}
                        </TableCell>
                        <TableCell className="text-right font-mono text-[#0066ff]">
                          {formatCompactCurrency(cliente.dias60)}
                        </TableCell>
                        <TableCell className="text-right font-mono text-[#ff0066]">
                          {formatCompactCurrency(cliente.dias90)}
                        </TableCell>
                        <TableCell className="text-right font-mono font-700 text-[#ff0066]">
                          {formatCompactCurrency(cliente.mas90)}
                        </TableCell>
                        <TableCell className="text-center">
                          <Badge
                            variant="outline"
                            className={`font-mono text-xs font-600 ${getRiskColor(
                              cliente.riesgo
                            )} bg-transparent`}>
                            {cliente.riesgo}
                          </Badge>
                        </TableCell>
                        <TableCell className="text-center">
                          {getTrendIcon(cliente.tendencia)}
                        </TableCell>
                        <TableCell className="text-center font-mono text-[#888888]">
                          {cliente.facturas}
                        </TableCell>
                        <TableCell className="font-mono text-sm text-[#888888]">
                          {new Date(cliente.ultimoPago).toLocaleDateString(
                            "es-CO"
                          )}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            </CardContent>
          </Card>

          {/* System Totals */}
          <Card className="bg-[#111111] border-[#00ff88] border-2">
            <CardContent className="p-8">
              <div className="overflow-x-auto">
                <Table>
                  <TableBody>
                    <TableRow className="border-none">
                      <TableCell className="font-700 text-[#00ff88] text-lg tracking-wider py-4 px-8">
                        SYSTEM TOTALS
                      </TableCell>
                      <TableCell className="text-right font-mono font-700 text-xl text-[#00ff88]">
                        {formatCompactCurrency(totales.total)}
                      </TableCell>
                      <TableCell className="text-right font-mono font-700 text-[#00ff88]">
                        {formatCompactCurrency(totales.corriente)}
                      </TableCell>
                      <TableCell className="text-right font-mono font-700 text-[#ffffff]">
                        {formatCompactCurrency(totales.dias30)}
                      </TableCell>
                      <TableCell className="text-right font-mono font-700 text-[#0066ff]">
                        {formatCompactCurrency(totales.dias60)}
                      </TableCell>
                      <TableCell className="text-right font-mono font-700 text-[#ff0066]">
                        {formatCompactCurrency(totales.dias90)}
                      </TableCell>
                      <TableCell className="text-right font-mono font-700 text-[#ff0066]">
                        {formatCompactCurrency(totales.mas90)}
                      </TableCell>
                      <TableCell className="text-center text-[#888888]">
                        -
                      </TableCell>
                      <TableCell className="text-center text-[#888888]">
                        -
                      </TableCell>
                      <TableCell className="text-center font-mono font-700 text-[#00ff88]">
                        {totales.facturas}
                      </TableCell>
                      <TableCell className="text-[#888888]">-</TableCell>
                    </TableRow>
                  </TableBody>
                </Table>
              </div>
            </CardContent>
          </Card>
        </div>
      </main>
    </div>
  );
}
