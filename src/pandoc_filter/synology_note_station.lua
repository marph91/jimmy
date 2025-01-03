function Image(img)
    -- In the original data, the "src" is stored in the "ref" attribute. Move it where it belongs.
    if img.attributes["ref"] then
        img.src = img.attributes["ref"]
    end
    return img
end
