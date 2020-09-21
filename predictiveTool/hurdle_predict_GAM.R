#Read in training data
data<-read.table(file.choose(),header=T,sep="\t") #Browse to and select R:\Projects\Habitat\PredictiveTool\GroupsData1213.txt at prompt 
#exclude Effort and Depth outliers
data<-subset(data, Effort<340)
data<-subset(data, Depth<70)
dim(data) #should now contain 56143 rows and 19 columns
attach(data)
head(data) #preview data frame

#install.packages('mgcv') #install package, if necessary
library('mgcv') #load package

#Run final selected GAM. k=3 limits d.f. to restrain wiggliness
#Binomial model for presence/absence, using all training data
m1<-gam(Presence~s(Effort,k=3)+s(SST,k=3)+s(DistToShore,k=3)+s(Depth,k=3)+s(DistTo22Iso,k=3)+te(SemiMonth,Northing,k=3)+Year,data=data,family=quasibinomial)
summary(m1) #view results; make sure 'Deviance explained'=22.8% and 'GCV score'=0.26416

#2nd GAM for # of whales, only using data with whales present
whales<-subset(data, Presence>0)
m3<-gam(OnWhales~te(SemiMonth,Northing,k=3)+Year+s(SST,k=3)+s(DistTo22Iso,k=3)+s(DistToShore,k=3)+s(Depth,k=3),data=whales,family=Gamma(link='log'))
summary(m3) #view results; make sure 'Deviance explained'=12.2% and 'GCV score'=0.40537


###Generate predictions
#Read in data
predict<-read.table(file.choose(),header=T,sep="\t") #Browse to and select your .txt file at prompt
head(predict) #preview data frame
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

#Export the predictions to .txt file
#install.packages('MASS') #install package, if necessary
library('MASS') #load package
write.matrix(predict,"C:\\Hab_Model_PredTool\\1920\\2019_Nov_27-30\\predict.txt") #export data frame with predictions