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


function hideLayerSet(layers)
{
    for (var i = 0; i < layers.length; i++)
    {
        var layer = layers[i];
        if (layer.typename == "LayerSet")
        {
            hideLayerSet(layer.layers);
        }
        if (layer.visible)
        {
            layer.visible = false;
        }
    }
}


function saveDocument()
{
    app.activeDocument.save();
}
