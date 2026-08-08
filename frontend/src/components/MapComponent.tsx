"use client";

import { useMemo } from 'react';
import { GoogleMap, useLoadScript, MarkerF, InfoWindowF } from '@react-google-maps/api';
import { useState } from 'react';

interface MapComponentProps {
  mapData: any[];
}

const mapContainerStyle = {
  width: '100%',
  height: '100%',
};

const defaultCenter = {
  lat: 28.6139,
  lng: 77.2090
};

export default function MapComponent({ mapData }: MapComponentProps) {
  const { isLoaded, loadError } = useLoadScript({
    googleMapsApiKey: process.env.NEXT_PUBLIC_GOOGLE_MAPS_API_KEY as string,
  });

  const [selectedMarker, setSelectedMarker] = useState<any | null>(null);

  // Map styles to make it look clean
  const options = useMemo(() => ({
    disableDefaultUI: false,
    clickableIcons: true,
    scrollwheel: true,
  }), []);

  if (loadError) {
    return <div className="w-full h-full flex items-center justify-center text-red-500 bg-red-50">Error loading Google Maps</div>;
  }

  if (!isLoaded) {
    return <div className="w-full h-full flex items-center justify-center bg-muted/20">Loading Map...</div>;
  }

  const getMarkerIcon = (status: string) => {
    let color = '#22c55e'; // green
    if (status === 'Warning') color = '#eab308'; // yellow
    if (status === 'Critical') color = '#ef4444'; // red
    
    return {
      path: "M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z",
      fillColor: color,
      fillOpacity: 1,
      strokeWeight: 1,
      strokeColor: '#ffffff',
      rotation: 0,
      scale: 1.5,
      anchor: new window.google.maps.Point(12, 22),
    };
  };

  // Center the map on the first marker if available, else default
  const center = mapData.length > 0 && mapData[0].latitude ? { lat: mapData[0].latitude, lng: mapData[0].longitude } : defaultCenter;

  return (
    <div style={{ height: '100%', width: '100%', position: 'relative' }}>
      <GoogleMap
        mapContainerStyle={mapContainerStyle}
        zoom={mapData.length > 0 ? 11 : 10}
        center={center}
        options={options}
        onClick={() => setSelectedMarker(null)}
      >
        {mapData.map((marker) => {
          if (marker.latitude === undefined || marker.latitude === null || marker.longitude === undefined || marker.longitude === null) return null;
          return (
            <MarkerF
              key={marker.id}
              position={{ lat: marker.latitude, lng: marker.longitude }}
              icon={getMarkerIcon(marker.status)}
              onClick={() => setSelectedMarker(marker)}
            />
          );
        })}

        {selectedMarker && (
          <InfoWindowF
            position={{ lat: selectedMarker.latitude, lng: selectedMarker.longitude }}
            onCloseClick={() => setSelectedMarker(null)}
          >
            <div className="p-1 max-w-[200px] text-foreground">
              <h4 className="font-bold text-sm mb-1">{selectedMarker.name}</h4>
              <p className="text-xs text-gray-600 mb-2">{selectedMarker.type} • Status: {selectedMarker.status}</p>
              <p className="text-xs font-semibold text-indigo-700 bg-indigo-50 px-2 py-1 rounded inline-block">Health Score: {selectedMarker.health_score}/100</p>
            </div>
          </InfoWindowF>
        )}
      </GoogleMap>
    </div>
  );
}
