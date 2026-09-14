import reference from '../../models/neighborhoods_v1.json';

// Empty selection is the explicit unlisted UI choice, never editable text.
// The fitted transformer uses Rare for unseen values (missing uses Unknown).
export const OTHER_NEIGHBORHOOD = '';
export const neighborhoodsByCity: Record<string, string[]> = reference;
export const neighborhoodLabel = (value: string) => value.normalize('NFC').replace(/\s+/g, ' ').trim();
const searchKey = (value: string) => neighborhoodLabel(value).normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLocaleLowerCase('fr');
export function neighborhoodOptions(city: string, query = '') {
  return (neighborhoodsByCity[city] || [])
    .filter(value => searchKey(value).includes(searchKey(query)))
    .map(value => ({ value, label: neighborhoodLabel(value) }))
    .sort((a, b) => a.label.localeCompare(b.label, 'fr'));
}
export function compatibleNeighborhood(city: string, value: string) {
  return (neighborhoodsByCity[city] || []).includes(value) ? value : OTHER_NEIGHBORHOOD;
}
export function neighborhoodForApi(city: string, value: string) {
  return compatibleNeighborhood(city, value) || 'Rare';
}
