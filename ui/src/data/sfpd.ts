// San Francisco, CA coordinates
export const SF_CENTER: [number, number] = [37.7749, -122.4194];

// Common SF Neighborhoods mapped as Risk Zones
export const SF_ZONES = [
  { id: 'tenderloin', name: 'Tenderloin', risk: 88 },
  { id: 'mission', name: 'Mission District', risk: 78 },
  { id: 'soma', name: 'South of Market', risk: 75 },
  { id: 'bayview', name: 'Bayview', risk: 65 },
  { id: 'financial', name: 'Financial District', risk: 45 },
  { id: 'richmond', name: 'Richmond District', risk: 25 },
  { id: 'sunset', name: 'Sunset District', risk: 30 },
  { id: 'marina', name: 'Marina District', risk: 35 },
];

export function getRiskColor(risk: number): string {
  if (risk >= 80) return '#dc2626';
  if (risk >= 60) return '#f59e0b';
  if (risk >= 40) return '#eab308';
  if (risk >= 20) return '#22c55e';
  return '#10b981';
}

export interface SfpdIncident {
  incident_id: string;
  incident_datetime: string;
  incident_category: string;
  incident_subcategory: string;
  incident_description: string;
  analysis_neighborhood: string;
  latitude: string;
  longitude: string;
}

export async function fetchLiveIncidents(limit: number = 100) {
  try {
    const response = await fetch(`https://data.sfgov.org/resource/wg3w-h783.json?$limit=${limit}&$order=incident_datetime%20DESC&$where=latitude IS NOT NULL`);
    if (!response.ok) throw new Error('Network response was not ok');
    const data: SfpdIncident[] = await response.json();
    
    return data.map((inc) => {
      // Rough severity mapping based on category
      let severity = 'Low';
      const category = (inc.incident_category || '').toLowerCase();
      if (category.includes('assault') || category.includes('robbery') || category.includes('weapon') || category.includes('homicide')) {
        severity = 'Critical';
      } else if (category.includes('burglary') || category.includes('vehicle') || category.includes('arson')) {
        severity = 'High';
      } else if (category.includes('larceny') || category.includes('theft') || category.includes('fraud')) {
        severity = 'Medium';
      }

      return {
        id: inc.incident_id || crypto.randomUUID(),
        type: inc.incident_category || 'Other',
        severity,
        location: [parseFloat(inc.latitude), parseFloat(inc.longitude)] as [number, number],
        address: inc.analysis_neighborhood || 'San Francisco',
        timestamp: new Date(inc.incident_datetime),
        description: inc.incident_description || 'Incident reported',
      };
    });
  } catch (error) {
    console.error('Error fetching SFPD data:', error);
    return [];
  }
}
