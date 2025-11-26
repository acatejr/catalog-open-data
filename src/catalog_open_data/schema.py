from pydantic import BaseModel
from typing import List, Optional


class SpatialReference(BaseModel):
    """
    Represents a spatial reference system for geospatial data.
    Attributes:
        wkid (Optional[int]): The well-known ID (WKID) of the spatial reference.
        latestWkid (Optional[int]): The latest well-known ID (WKID) for the spatial reference.
        xyTolerance (Optional[float]): The minimum distance between coordinates before they are considered equal in the XY plane.
        zTolerance (Optional[float]): The minimum distance between Z values before they are considered equal.
        mTolerance (Optional[float]): The minimum distance between M values before they are considered equal.
        falseX (Optional[float]): The X coordinate of the origin for the spatial reference.
        falseY (Optional[float]): The Y coordinate of the origin for the spatial reference.
        xyUnits (Optional[float]): The units for the XY coordinates.
        falseZ (Optional[float]): The Z coordinate of the origin for the spatial reference.
        zUnits (Optional[float]): The units for the Z coordinates.
        falseM (Optional[float]): The M coordinate of the origin for the spatial reference.
        mUnits (Optional[float]): The units for the M coordinates.
    """

    wkid: Optional[int] = None
    latestWkid: Optional[int] = None
    xyTolerance: Optional[float] = None
    zTolerance: Optional[float] = None
    mTolerance: Optional[float] = None
    falseX: Optional[float] = None
    falseY: Optional[float] = None
    xyUnits: Optional[float] = None
    falseZ: Optional[float] = None
    zUnits: Optional[float] = None
    falseM: Optional[float] = None
    mUnits: Optional[float] = None


class Extent(BaseModel):
    """
    Extent represents a rectangular bounding box defined by minimum and maximum X and Y coordinates,
    optionally associated with a spatial reference system.
    Attributes:
        xmin (Optional[float]): The minimum X coordinate (longitude or easting) of the extent.
        ymin (Optional[float]): The minimum Y coordinate (latitude or northing) of the extent.
        xmax (Optional[float]): The maximum X coordinate (longitude or easting) of the extent.
        ymax (Optional[float]): The maximum Y coordinate (latitude or northing) of the extent.
        spatialReference (Optional[SpatialReference]): The spatial reference system associated with the extent.
    """

    xmin: Optional[float] = None
    ymin: Optional[float] = None
    xmax: Optional[float] = None
    ymax: Optional[float] = None
    spatialReference: Optional[SpatialReference] = None


class Layer(BaseModel):
    """
    Represents a map layer with optional metadata and configuration.
    Attributes:
        id (Optional[int]): Unique identifier for the layer.
        name (Optional[str]): Name of the layer.
        parentLayerId (Optional[int]): Identifier of the parent layer, if any.
        defaultVisibility (Optional[bool]): Indicates if the layer is visible by default.
        subLayerIds (Optional[List[int]]): List of identifiers for sublayers.
        minScale (Optional[float]): Minimum scale at which the layer is visible.
        maxScale (Optional[float]): Maximum scale at which the layer is visible.
        type (Optional[str]): Type of the layer (e.g., "Feature Layer", "Raster Layer").
        geometryType (Optional[str]): Type of geometry contained in the layer (e.g., "Point", "Polygon").
        supportsDynamicLegends (Optional[bool]): Indicates if the layer supports dynamic legends.
    """

    id: Optional[int] = None
    name: Optional[str] = None
    parentLayerId: Optional[int] = None
    defaultVisibility: Optional[bool] = None
    subLayerIds: Optional[List[int]] = None
    minScale: Optional[float] = None
    maxScale: Optional[float] = None
    type: Optional[str] = None
    geometryType: Optional[str] = None
    supportsDynamicLegends: Optional[bool] = None


class DocumentInfo(BaseModel):
    Title: Optional[str] = None
    Author: Optional[str] = None
    Comments: Optional[str] = None
    Subject: Optional[str] = None
    Category: Optional[str] = None
    Version: Optional[str] = None
    AntialiasingMode: Optional[str] = None
    TextAntialiasingMode: Optional[str] = None
    Keywords: Optional[str] = None


class ArchivingInfo(BaseModel):
    """
    Represents information about the archiving capabilities of a dataset.
    Attributes:
        supportsHistoricMoment (Optional[bool]): Indicates whether the dataset supports querying or retrieving data as it existed at a specific point in time (historic moment). If None, this information is unspecified.
    """

    supportsHistoricMoment: Optional[bool] = None


class MapUnits(BaseModel):
    """
    Represents a mapping unit with an optional unique identifier.

    Attributes:
        uwkid (Optional[int]): Unique identifier for the map unit. Defaults to None if not provided.
    """

    uwkid: Optional[int] = None


class MapServer(BaseModel):
    """
    Represents the schema for a MapServer resource, typically used in GIS applications to describe the properties and capabilities of a map service.

    Attributes:
        currentVersion (Optional[float]): The current version of the MapServer.
        cimVersion (Optional[str]): The CIM (Cartographic Information Model) version.
        serviceDescription (Optional[str]): A description of the map service.
        mapName (Optional[str]): The name of the map.
        description (Optional[str]): Additional description of the map service.
        copyrightText (Optional[str]): Copyright information for the map data.
        supportsDynamicLayers (Optional[bool]): Indicates if dynamic layers are supported.
        layers (Optional[List[Layer]]): List of map layers.
        tables (Optional[List[dict]]): List of tables associated with the map service.
        spatialReference (Optional[SpatialReference]): The spatial reference system used by the map.
        singleFusedMapCache (Optional[bool]): Indicates if a single fused map cache is used.
        initialExtent (Optional[Extent]): The initial extent of the map.
        fullExtent (Optional[Extent]): The full extent of the map.
        datesInUnknownTimezone (Optional[bool]): Indicates if dates are in an unknown timezone.
        minScale (Optional[float]): The minimum scale at which the map is visible.
        maxScale (Optional[float]): The maximum scale at which the map is visible.
        units (Optional[str]): The units of measurement for the map.
        supportedImageFormatTypes (Optional[str]): Supported image format types for export.
        documentInfo (Optional[DocumentInfo]): Additional document information.
        supportsQueryDomains (Optional[bool]): Indicates if query domains are supported.
        capabilities (Optional[str]): Capabilities supported by the map service.
        supportedQueryFormats (Optional[str]): Supported query formats.
        exportTilesAllowed (Optional[bool]): Indicates if tile export is allowed.
        referenceScale (Optional[float]): The reference scale for the map.
        supportsDatumTransformation (Optional[bool]): Indicates if datum transformation is supported.
        archivingInfo (Optional[ArchivingInfo]): Information about data archiving.
        supportsClipping (Optional[bool]): Indicates if clipping is supported.
        supportsSpatialFilter (Optional[bool]): Indicates if spatial filtering is supported.
        supportsTimeRelation (Optional[bool]): Indicates if time relation queries are supported.
        supportsQueryDataElements (Optional[bool]): Indicates if querying data elements is supported.
        mapUnits (Optional[MapUnits]): The map units used.
        maxRecordCount (Optional[int]): Maximum number of records that can be returned in a query.
        maxImageHeight (Optional[int]): Maximum height of exported images.
        maxImageWidth (Optional[int]): Maximum width of exported images.
        supportedExtensions (Optional[str]): Supported extensions for the map service.
        resampling (Optional[bool]): Indicates if resampling is supported.
    """

    currentVersion: Optional[float] = None
    cimVersion: Optional[str] = None
    serviceDescription: Optional[str] = None
    mapName: Optional[str] = None
    description: Optional[str] = None
    copyrightText: Optional[str] = None
    supportsDynamicLayers: Optional[bool] = None
    layers: Optional[List[Layer]] = None
    tables: Optional[List[dict]] = None  # Assuming tables are dicts, empty in example
    spatialReference: Optional[SpatialReference] = None
    singleFusedMapCache: Optional[bool] = None
    initialExtent: Optional[Extent] = None
    fullExtent: Optional[Extent] = None
    datesInUnknownTimezone: Optional[bool] = None
    minScale: Optional[float] = None
    maxScale: Optional[float] = None
    units: Optional[str] = None
    supportedImageFormatTypes: Optional[str] = None
    documentInfo: Optional[DocumentInfo] = None
    supportsQueryDomains: Optional[bool] = None
    capabilities: Optional[str] = None
    supportedQueryFormats: Optional[str] = None
    exportTilesAllowed: Optional[bool] = None
    referenceScale: Optional[float] = None
    supportsDatumTransformation: Optional[bool] = None
    archivingInfo: Optional[ArchivingInfo] = None
    supportsClipping: Optional[bool] = None
    supportsSpatialFilter: Optional[bool] = None
    supportsTimeRelation: Optional[bool] = None
    supportsQueryDataElements: Optional[bool] = None
    mapUnits: Optional[MapUnits] = None
    maxRecordCount: Optional[int] = None
    maxImageHeight: Optional[int] = None
    maxImageWidth: Optional[int] = None
    supportedExtensions: Optional[str] = None
    resampling: Optional[bool] = None
