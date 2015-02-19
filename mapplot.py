"""Plot regions from a shapefile on a map and color based on values."""
from mpl_toolkits.basemap import Basemap
from matplotlib import cm
from matplotlib.collections import LineCollection
from collections import defaultdict
import warnings


class MapPlot(Basemap):
    """Class to plot map with regions."""

    def __init__(self,continent_color='0.9',**kwargs):
        if 'ax' not in kwargs:
            raise ValueError("An axes object must be given.")
        super(MapPlot, self).__init__(**kwargs)

        self.defaults = {
            "region_style": {
                "edgecolors": "k",
                "linewidth": 0.2,
                "facecolor": "white"
            },
            "colormap": cm.Blues,
            "linestyle": {
                "linewidth": 2,
                "color": "0.2"
            },
            "markerstyle": {
                "marker": 'o',
                "markersize": 4     ,
                "markeredgecolor": "k",
                "markerfacecolor": "0.8"
            },
            "text_props": {
                "horizontalalignment": "center",
                "verticalalignment": "center" 
            }
        }
        
        if continent_color and self.resolution:
            self.fillcontinents(color=continent_color)

        self.set_axes_limits()

    def _with_defaults(self,key,new):
        """Create new dict of settings based on default and new."""
        out = self.defaults[key].copy()
        out.update(new)
        return out

    def load_regions(self,shp_file,**kwargs):
        """Load the regions to plot on map."""
        self._read_shp(shp_file,'regs',**kwargs)

    def load_data(self,shp_file,attr,**kwargs):
        """Load data from shapefile into attr."""
        self._read_shp(shp_file,attr,**kwargs)

    def _read_shp(self,shp_file,attr,key_fcn,filter_fcn=None):
        """Read data from shapefile into dictionary grouping by key_fcn
        and filtering by filter_fcn."""
        shape_info = self.readshapefile(shp_file,'_shapes',drawbounds=False)

        setattr(self,attr,defaultdict(list))
        for shapedict,shape in zip(self._shapes_info,self._shapes):
            key = key_fcn(shapedict)
            # Check filter if given
            if not filter_fcn or filter_fcn(shapedict):
                getattr(self,attr)[key].append(shape)

    def draw_regions(self,**region_style):
        """Draw region shapes on axes and save line collection in dictionary."""
        if not hasattr(self,'regs'):
            raise AttributeError("Regions must be loaded "
                                    "before they can be drawn.")

        lc_args = self._with_defaults("region_style",region_style)
        self.reg_lcs = {}
        for key,segs in self.regs.iteritems():
            lc = LineCollection(segs,antialiaseds=(1,))
            lc.set(**lc_args)
            self.ax.add_collection(lc)

            self.reg_lcs[key] = lc

    def draw_texts(self,coords,texts=None,**kwargs):
        """Draw a text for each item in dict of coordinates. Defaults to using 
        region keys as texts."""
        if not texts:
            texts = dict(zip(self.regs.keys(),self.regs.keys()))

        text_props = self._with_defaults("text_props",kwargs)
        for r,(x,y) in coords.iteritems():
            try:
                self.ax.text(x,y,texts[r],**text_props)
            except KeyError as e:
                warnings.warn("No text for '{}'.".format(r))

    def draw_points(self,coords,**kwargs):
        """Draw points from a list of coordinates (x,y)."""
        markerstyle = self._with_defaults("markerstyle",kwargs)
        xs,ys = zip(*coords)
        self.plot(xs,ys,linestyle='none',**markerstyle)
        
    def draw_lines(self,points,lines,all_points=False,**kwargs):
        """Draw lines between selected points from 'points'."""

        # Draw lines between each selected pair of points
        for (p1,p2),styles in lines.iteritems():
            linestyle = self._with_defaults("linestyle",styles)
            xs,ys = zip(points[p1],points[p2])
            self.plot(xs,ys,**linestyle)

        if all_points:
            plot_points = points.values()
        else:
            # Draw each point once
            plot_points = [points[p] for p in set(sum(lines.keys(),()))]
        self.draw_points(plot_points,**kwargs)

    def color_regions(self,reg_colors):
        """Set facecolor for each region in reg_colors."""
        if not hasattr(self,'reg_lcs'):
            raise AttributeError("Regions must be drawn "
                                    "before they can be colored.")

        for r,c in reg_colors.iteritems():
            self.reg_lcs[r].set_facecolor(c)

    def color_from_values(self,val_dict,clims=None,cblabel=None,colormap=None):
        """Fill regions based on values in val_dict and colormap."""
        cmap = self.default_colormap if not colormap else colormap
        self.sm = cm.ScalarMappable(cmap=cmap)
        self.sm.set_array(list(clims) if clims else val_dict.values())
        self.sm.autoscale()

        # Map colormap over dict values and call color_regions
        self.color_regions({r: self.sm.to_rgba(val) 
                                for r,val in val_dict.iteritems()})

    def add_colorbar(self,label=None,**kwargs):
        """Add a colorbar to the map."""
        cb = self.colorbar(self.sm)
        if label:
            cb.set_label(label)
        