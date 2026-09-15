/*
photoshop_export.jsx

Photoshop automation:
- Export PNG preview from a fresh duplicate (captures current state)
- Hide only visible layers (respect already-hidden layers)
- Save document
*/


function exportPreview(path)
{
    var doc = app.activeDocument;
    // Duplicate so we render the current in-memory state without
    // modifying the original document's format or layers.
    var tmp = doc.duplicate();
    tmp.flatten();
    var options = new PNGSaveOptions();
    var file = new File(path);
    tmp.saveAs(file, options, true, Extension.LOWERCASE);
    tmp.close(SaveOptions.DONOTSAVECHANGES);
}


function hideVisibleLayers()
{
    var doc = app.activeDocument;
    hideLayerSet(doc.layers);
}


function unlockLayer(layer)
{
    // Unlock every lock kind first: a single allLocked/positionLocked
    // layer throws on `visible = false` and aborts the whole loop,
    // leaving random layers visible (and the file big). Each attempt
    // is isolated so unknown properties on a build never stop us.
    try { layer.allLocked = false; } catch (e) {}
    try { layer.locked = false; } catch (e) {}
    try { layer.pixelsLocked = false; } catch (e) {}
    try { layer.positionLocked = false; } catch (e) {}
    try { layer.transparentPixelsLocked = false; } catch (e) {}
}


function hideLayerSet(layers)
{
    for (var i = 0; i < layers.length; i++)
    {
        var layer = layers[i];
        try { unlockLayer(layer); } catch (e) {}
        if (layer.typename == "LayerSet")
        {
            // Unlock + hide children first, then the group itself.
            try { hideLayerSet(layer.layers); } catch (e) {}
        }
        try
        {
            if (layer.visible)
            {
                layer.visible = false;
            }
        }
        catch (e)
        {
            // One stubborn layer (e.g. background) must never abort
            // the rest — continue hiding everything else.
        }
    }
}


function saveDocument()
{
    app.activeDocument.save();
}
