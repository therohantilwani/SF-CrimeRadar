// Stockton, CA coordinates
export const STOCKTON_CENTER: [number, number] = [37.9577, -121.2908];
export const STOCKTON_BOUNDS = {
  north: 38.05,
  south: 37.85,
  east: -121.15,
  west: -121.45,
};

// Crime type definitions
export const CRIME_TYPES = [
  'Theft',
  'Burglary',
  'Assault',
  'Robbery',
  'Vandalism',
  'Drug Offense',
  'Weapons',
  'Vehicle Theft',
] as const;

export type CrimeType = typeof CRIME_TYPES[number];

// Severity levels
export const SEVERITY_LEVELS = ['Low', 'Medium', 'High', 'Critical'] as const;
export type SeverityLevel = typeof SEVERITY_LEVELS[number];

// Risk zones in Stockton
export const STOCKTON_ZONES = [
  { id: 'downtown', name: 'Downtown Stockton', risk: 85 },
  { id: 'east-side', name: 'East Side', risk: 72 },
  { id: 'south-stockton', name: 'South Stockton', risk: 68 },
  { id: 'north-stockton', name: 'North Stockton', risk: 45 },
  { id: 'brookside', name: 'Brookside', risk: 25 },
  { id: 'weberstown', name: 'Weberstown', risk: 35 },
  { id: 'magna', name: 'Magna', risk: 55 },
  { id: 'lakeview', name: 'Lakeview', risk: 30 },
];

// Generate random location in Stockton
export function randomStocktonLocation() {
  const lat = STOCKTON_BOUNDS.south + Math.random() * (STOCKTON_BOUNDS.north - STOCKTON_BOUNDS.south);
  const lng = STOCKTON_BOUNDS.west + Math.random() * (STOCKTON_BOUNDS.east - STOCKTON_BOUNDS.west);
  return [lat, lng] as [number, number];
}

// Generate random crime incident
export function generateIncident() {
  const types = [...CRIME_TYPES];
  const severities = [...SEVERITY_LEVELS];
  
  return {
    id: crypto.randomUUID(),
    type: types[Math.floor(Math.random() * types.length)],
    severity: severities[Math.floor(Math.random() * severities.length)],
    location: randomStocktonLocation(),
    address: `${Math.floor(Math.random() * 9000) + 1000} ${['Main St', 'El Dorado St', 'Pacific Ave', 'San Joaquin St', 'Weber Ave', 'Hammer Ln', 'March Ln'][Math.floor(Math.random() * 7)]}`,
    timestamp: new Date(Date.now() - Math.random() * 24 * 60 * 60 * 1000),
    description: `Reported ${types[Math.floor(Math.random() * types.length)].toLowerCase()} incident`,
  };
}

// Generate incidents for a time period
export function generateIncidents(count: number) {
  return Array.from({ length: count }, () => generateIncident());
}

// Zone colors based on risk
export function getRiskColor(risk: number): string {
  if (risk >= 80) return '#dc2626';
  if (risk >= 60) return '#f59e0b';
  if (risk >= 40) return '#eab308';
  if (risk >= 20) return '#22c55e';
  return '#10b981';
}
