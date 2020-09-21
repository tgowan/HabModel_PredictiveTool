
# note: sstavg and processed SST rasters are not saved/exported

# note: Cannot write to PredictiveTool.gdb. And saving results as shapfile is problematic.
# So will need to join 'outf.csv' or 'enviro.gpkg/HabModelEnviro' to 'HabModelEnviro' and 'HabModelPrediction' in Arc after this R script is run

biweek = 'Jan20B'
biweekt = 'JanB'
semimonth = 4 # 1-8, corresponding to DecA-MarB

#directory with SST and Cloud folders containing unzipped .hdr/.flt files
setwd("C:/Users/tim.gowan/Documents/Working/SST/Jan01thru15") 
#setwd("R:/Data/SST/CoastWatch_CaribNode/cw1920/Biweeks/JanB/Pred_Model/2020_Jan_13-16")

#directory for PredictiveTool.gdb
gdb = "C:/Users/tim.gowan/Documents/Working/SST/Jan01thru15/PredictiveTool.gdb"
#gdb = "R:/Projects/Habitat/PredictiveTool/PredictiveTool.gdb"


#################

#install.packages('mgcv') #install packages, if necessary
library(raster)
library(rgdal)
library(rgeos)
library(mgcv)


#################
# a1: Create 'sstavg' raster


# list all SST (and cloud) files in directory
sst <- list.files(path="SST", pattern = ".flt")
cloud <- list.files(path="Cloud", pattern = ".flt")
length(sst) #number of images

# loop through and process each image
sstList <- vector("list", length(sst)) # new list to store processed data
for (t in 1:length(sst)){
  a <- raster(paste0("SST/", sst[t])) #covert SST float to raster
  a[is.na(a)] <- 0 # set NA values as 0
  
  c <- raster(paste0("Cloud/", sst[t])) #covert cloud float to raster
  c[is.na(c)] <- 0 # set NA values as 0
  c[c < 0.1] <- -99 # recode values to 1 or 0
  c[c > -99] <- 0
  c[c == -99] <- 1
  
  x <- a * c #multiply SST image by cloud mask
  x[x < 5] <- NA # set values <5 degrees C as Null
  
  sstList[[t]] <- x #save
}

# store each in RasterLayer
b <- sstList[[1]]
for (t in 2:length(sst)){
  b <- stack(b, sstList[[t]])
}

# Create average
sstavg <- mean(b, na.rm=T)
plot(sstavg)

# Define projection (WGS 1984 Mercator)
crs(sstavg) <- "+proj=merc +lon_0=0 +k=1 +x_0=0 +y_0=0 +ellps=WGS84 +datum=WGS84 +units=m +no_defs"


#################
# a2: Summarize 'sstavg' raster into fishnet grid. 

enviro = readOGR(gdb,"HabModelEnviro") #read in fishnet

r.vals <- extract(sstavg, enviro) #Extract raster values to list object
r.mean <- unlist(lapply(r.vals, mean, na.rm=TRUE)) # Use list apply to calculate mean for each grid cell
enviro@data <- data.frame(enviro@data, mean=r.mean)  # Join mean values to fishnet
spplot(enviro, "mean")


#################
# a3: Create isotherms and calculate distance to 22oC isotherm

front_fish = readOGR(gdb,"front_fishnetC") #read in front fishnet
f.vals <- extract(sstavg, front_fish) #Extract raster values to list object
f.mean <- unlist(lapply(f.vals, mean, na.rm=TRUE)) # Use list apply to calculate mean for each grid cell
front_fish@data <- data.frame(front_fish@data, mean=f.mean)  # Join mean values to fishnet

#convert fishnet to raster
fr <- raster(xmn=min(coordinates(front_fish)[,1]), xmx=max(coordinates(front_fish)[,1]), 
            ymn=min(coordinates(front_fish)[,2]), ymx=max(coordinates(front_fish)[,2]), 
            res=4200)
values(fr) <- 1:ncell(fr) #raster value = cell number
r.polys <- rasterize(front_fish, fr, field=front_fish@data$mean, fun=mean)

#create contour lines
cl <- rasterToContour(r.polys, levels=c(12,16,22))
plot(r.polys)
plot(cl, add=TRUE)
cl22 <- cl[cl@data$level==22,]
plot(cl22, add=TRUE, col='red', lwd=3)
#writeOGR(cl, getwd(), "cl", driver="ESRI Shapefile", check_exists=TRUE, overwrite_layer=TRUE)

#distance from 22 isotherm to centroids of grid cells
centroids = readOGR(gdb,"centroids") #read in cell centroids
m <- gDistance(centroids, cl22, byid=TRUE) #calculate distance
centroids@data <- data.frame(centroids@data, dist=m[1,])  # Join distance values to centroids

#join values to fishnet
enviro@data$id  <- 1:nrow(enviro@data) #to preserve order of rows in fishnet feature class
out  <- merge(enviro@data, centroids@data, by="FishnetID")
out <- out[order(out$id), ]
enviro@data <- out

# change to negative value if mean >=22 degrees
enviro@data$dist[enviro@data$mean >= 22 & !is.na(enviro@data$mean)] <- -1*enviro@data$dist[enviro@data$mean >= 22 & !is.na(enviro@data$mean)]
spplot(enviro, "dist", col = "transparent", sp.layout=list(cl22, lwd=3))


#################
# steps 4,5,6: SQL query

#extract data within prediction range
sub <- enviro@data[(enviro@data$NEAR_DIST/1000 > 0 & enviro@data$NEAR_DIST/1000 <= 77.47) &
                   ((enviro@data$MEAN_depth * -1) > 2 & (enviro@data$MEAN_depth * -1) < 69.86) &
                   (enviro@data$POINT_Y >= 2966814 & enviro@data$POINT_Y <= 3743524) & 
                   (enviro@data$POINT_X >= 457819.5 & enviro@data$POINT_X <= 761227.2) & 
                    enviro@data$mean > 5 & !is.na(enviro@data$dist),
                   c('X', 'Y', 'POINT_X', 'POINT_Y', 'Zone', 'MEAN_depth', 'MEAN_slope', 'NEAR_DIST',
                     'FishnetID', 'mean', 'dist')]

#remove cells with missing data
sub <- sub[!is.na(sub$mean),]
#rename columns, convert dist to km
predict <- data.frame(Long=sub$X, Lat=sub$Y, Easting=sub$POINT_X, Northing=sub$POINT_Y, Zone=sub$Zone,
                   Depth=(sub$MEAN_depth * -1), Slope=sub$MEAN_slope, DistToShore=(sub$NEAR_DIST/1000),
                   FishnetID=sub$FishnetID, Biweek=biweek, BiweekT=biweekt, SemiMonth=semimonth,
                   Year='08_09', SST=sub$mean, DistTo22Iso=sub$dist/1000, Effort=250)


#################
# steps 7-8: generate predictions

#Read in training data
data<-read.table("R:/Projects/Habitat/PredictiveTool/GroupsData1213.txt", header=T,sep="\t")
#exclude Effort and Depth outliers
data<-subset(data, Effort<340)
data<-subset(data, Depth<70)
dim(data) #should now contain 56143 rows and 19 columns
head(data) #preview data frame

#Run final selected GAM. k=3 limits d.f. to restrain wiggliness
#Binomial model for presence/absence, using all training data
m1<-gam(Presence~s(Effort,k=3)+s(SST,k=3)+s(DistToShore,k=3)+s(Depth,k=3)+s(DistTo22Iso,k=3)+te(SemiMonth,Northing,k=3)+Year,data=data,family=quasibinomial)
summary(m1) #view results; make sure 'Deviance explained'=22.8% and 'GCV score'=0.264

#2nd GAM for # of whales, only using data with whales present
whales<-subset(data, Presence>0)
m3<-gam(OnWhales~te(SemiMonth,Northing,k=3)+Year+s(SST,k=3)+s(DistTo22Iso,k=3)+s(DistToShore,k=3)+s(Depth,k=3),data=whales,family=Gamma(link='log'))
summary(m3) #view results; make sure 'Deviance explained'=12.2% and 'GCV score'=0.405

###Generate predictions
dim(predict) #should contain ~1600 rows and 16 columns

#Predict presence/absence
predict$pres<-predict(m1,newdata=predict,type="response")
#Predict # of whales
predict$count<-predict(m3,newdata=predict,type="response")
#Calculate expected # of whales
predict$abund<-predict$pres*predict$count
#Calculate variance for expected # of whales
predict$var_abund<-(predict$pres*predict$count)+(predict$pres*predict$count^2)*(1-predict$pres)
head(predict) #note 4 new columns (pres, count, abund, and var_abund) were added to data frame

#Some plots to check to results
plot(predict$pres~predict$SST)
plot(predict$pres~predict$Depth)


#################
# step 9: join predictions to fishnet

out2  <- merge(enviro@data, predict[,c('FishnetID', 'pres', 'abund')], by="FishnetID", all=TRUE)
out2 <- out2[order(out2$id), ]
enviro@data <- out2
enviro@data$pres <- as.numeric(enviro@data$pres)
enviro@data$abund <- as.numeric(enviro@data$abund)
spplot(enviro, "pres", col = "transparent")

#rename columns
colnames(enviro@data)[colnames(enviro@data)=='mean'] <- paste0('mean_',biweek)
colnames(enviro@data)[colnames(enviro@data)=='dist'] <- paste0('Iso22',biweek)
colnames(enviro@data)[colnames(enviro@data)=='pres'] <- paste0(biweek,'Pres')
colnames(enviro@data)[colnames(enviro@data)=='abund'] <- paste0(biweek,'Abund')

# Write results (Note: cannot write to ESRI file gdb, but may be possible with 'arcgisbinding')
#writeOGR(enviro, getwd(), "HabModelEnviro", driver="ESRI Shapefile", check_exists=TRUE, overwrite_layer=TRUE)

#export as geopackage file
writeOGR(enviro, dsn="enviro.gpkg", layer="HabModelEnviro", driver="GPKG", check_exists=TRUE, overwrite_layer=TRUE)

# export as csv
outf <- enviro@data[,c('FishnetID', 'POINT_X', 'POINT_Y',
                       paste0('mean_',biweek), paste0('Iso22',biweek),
                       paste0(biweek,'Pres'), paste0(biweek,'Abund'))]
write.csv(outf, 'outf.csv')

#################
## Need to run a version of 'a4_Final_FeatureClass.py' to join 
#  meanSST and Iso22 fields to HabModelEnviro and
#  Pres and Abund fields to HabModelPredictions


