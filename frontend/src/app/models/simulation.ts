export interface Simulation {
  time: string;
  totalConsumptionMw: number;
  nuclearProductionMw: number;
  solarProductionMw: number;
  windProductionMw: number;
  availableReserveMw: number;
  unmetDemandMw: number;
  status: 'normal' | 'degraded' | 'insufficient';
}

export interface PlantState {
  id: string;
  name: string;
  powerMw: number;
  minPowerMw: number;
  maxPowerMw: number;
  availablePowerMw: number;
  rampUpMw: number;
  rampDownMw: number;
  saturationRate: number;
  available: boolean;
}